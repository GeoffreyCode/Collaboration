"""
更新管理器
负责客户端和服务端的更新检查、下载和安装
"""

import os
import json
import hashlib
import logging
import requests
import shutil
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import sys

logger = logging.getLogger(__name__)

class UpdateManager:
    """更新管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.update_url = f"{config.get('update_server')}{config.get('update_path')}"
        self.current_version = config.get('current_version')
        self.update_info = None
        self.download_progress = 0
        self.update_dir = Path("updates")
        self.update_dir.mkdir(exist_ok=True)
        
    def check_for_updates(self) -> Tuple[bool, Optional[Dict]]:
        """检查更新"""
        try:
            # 从更新服务器获取版本信息
            versions_url = f"{self.update_url}/versions.json"
            response = requests.get(versions_url, timeout=10)
            response.raise_for_status()
            
            versions_data = response.json()
            latest_version = versions_data.get('latest')
            update_info = versions_data.get('versions', {}).get(latest_version)
            
            if not update_info:
                logger.warning("未找到更新信息")
                return False, None
            
            # 比较版本
            if self.compare_versions(latest_version, self.current_version) > 0:
                logger.info(f"发现新版本: {latest_version} (当前: {self.current_version})")
                update_info['version'] = latest_version
                self.update_info = update_info
                return True, update_info
            else:
                logger.info("当前已是最新版本")
                return False, None
                
        except requests.RequestException as e:
            logger.error(f"检查更新失败: {e}")
            return False, None
        except json.JSONDecodeError as e:
            logger.error(f"解析更新信息失败: {e}")
            return False, None
        except Exception as e:
            logger.error(f"检查更新时发生错误: {e}")
            return False, None
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号"""
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        
        # 确保长度一致
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    
    def download_update(self, update_info: Dict, callback=None) -> bool:
        """下载更新"""
        try:
            version = update_info.get('version')
            filename = update_info.get('filename', f'collaboration_v{version}.zip')
            download_url = f"{self.update_url}/{version}/{filename}"
            
            logger.info(f"开始下载更新: {version}")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix=f"collaboration_update_{version}_")
            
            # 下载文件
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # 保存文件
            update_file = os.path.join(temp_dir, filename)
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.download_progress = progress
                            
                            if callback:
                                callback(progress, downloaded, total_size)
            
            # 验证文件哈希
            if not self.verify_file_hash(update_file, update_info.get('hash')):
                logger.error("文件哈希验证失败")
                shutil.rmtree(temp_dir)
                return False
            
            # 解压文件
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 保存更新信息
            update_info['temp_dir'] = temp_dir
            update_info['extract_dir'] = extract_dir
            update_info['downloaded_at'] = datetime.now().isoformat()
            self.update_info = update_info
            
            logger.info(f"更新下载完成: {version}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"下载更新失败: {e}")
            return False
        except zipfile.BadZipFile as e:
            logger.error(f"更新文件损坏: {e}")
            return False
        except Exception as e:
            logger.error(f"下载更新时发生错误: {e}")
            return False
    
    def verify_file_hash(self, filepath: str, expected_hash: str) -> bool:
        """验证文件哈希"""
        if not expected_hash:
            logger.warning("没有提供文件哈希，跳过验证")
            return True
            
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            actual_hash = sha256_hash.hexdigest()
            return actual_hash == expected_hash.lower()
            
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return False
    
    def install_update(self) -> bool:
        """安装更新"""
        if not self.update_info:
            logger.error("没有可安装的更新")
            return False
        
        try:
            version = self.update_info.get('version')
            extract_dir = self.update_info.get('extract_dir')
            temp_dir = self.update_info.get('temp_dir')
            
            if not os.path.exists(extract_dir):
                logger.error("更新文件不存在")
                return False
            
            logger.info(f"开始安装更新: {version}")
            
            # 备份当前版本
            if self.config.get('backup_enabled'):
                backup_dir = Path(f"backup_v{self.current_version}")
                backup_dir.mkdir(exist_ok=True)
                
                # 备份关键文件
                files_to_backup = [
                    'collaboration_client.py',
                    'collaboration_server.py',
                    'config.py',
                    'requirements.txt'
                ]
                
                for file in files_to_backup:
                    if os.path.exists(file):
                        shutil.copy2(file, backup_dir / file)
                
                logger.info(f"已备份当前版本到: {backup_dir}")
            
            # 查找更新包中的文件
            update_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.py') or file in ['requirements.txt', 'README.md']:
                        update_files.append(os.path.join(root, file))
            
            # 复制文件
            for update_file in update_files:
                rel_path = os.path.relpath(update_file, extract_dir)
                dest_path = Path(rel_path)
                
                # 确保目标目录存在
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(update_file, dest_path)
                logger.debug(f"复制文件: {rel_path}")
            
            # 更新配置文件中的版本号
            self.update_config_version(version)
            
            # 清理临时文件
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            logger.info(f"更新安装完成: {version}")
            return True
            
        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            return False
    
    def update_config_version(self, new_version: str):
        """更新配置文件中的版本号"""
        try:
            config_file = 'config.py'
            if not os.path.exists(config_file):
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找并更新版本号
            for i, line in enumerate(lines):
                if "'current_version'" in line or '"current_version"' in line:
                    # 找到版本行，提取并替换
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            lines[i] = f"    'current_version': '{new_version}',  # 当前版本\n"
                    break
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"配置文件版本号已更新为: {new_version}")
            
        except Exception as e:
            logger.error(f"更新配置文件版本号失败: {e}")
    
    def create_update_package(self, version: str, files: List[str], 
                            output_dir: str = "updates") -> Optional[str]:
        """创建更新包"""
        try:
            # 创建版本目录
            version_dir = Path(output_dir) / version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建临时目录用于打包
            temp_dir = tempfile.mkdtemp(prefix=f"update_package_{version}_")
            package_dir = Path(temp_dir) / f"collaboration_v{version}"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            for file_path in files:
                if os.path.exists(file_path):
                    dest_path = package_dir / os.path.basename(file_path)
                    shutil.copy2(file_path, dest_path)
            
            # 创建更新说明
            readme_file = package_dir / "UPDATE_README.txt"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"Collaboration 更新包 v{version}\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                f.write("包含的文件:\n")
                for file_path in files:
                    f.write(f"  - {os.path.basename(file_path)}\n")
            
            # 压缩为zip文件
            zip_filename = f"collaboration_v{version}.zip"
            zip_path = version_dir / zip_filename
            
            # 删除已存在的zip文件
            if zip_path.exists():
                zip_path.unlink()
            
            # 创建zip文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(package_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(package_dir)
                        zipf.write(file_path, arcname)
            
            # 计算文件哈希
            sha256_hash = hashlib.sha256()
            with open(zip_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()
            
            # 创建版本信息
            update_info = {
                'version': version,
                'filename': zip_filename,
                'hash': file_hash,
                'size': os.path.getsize(zip_path),
                'release_date': datetime.now().isoformat(),
                'description': f"Collaboration 版本 {version} 更新",
                'files': [os.path.basename(f) for f in files],
                'requires_restart': True
            }
            
            # 更新versions.json
            versions_file = Path(output_dir) / "versions.json"
            if versions_file.exists():
                with open(versions_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
            else:
                versions_data = {
                    'latest': version,
                    'versions': {}
                }
            
            versions_data['latest'] = version
            versions_data['versions'][version] = update_info
            
            with open(versions_file, 'w', encoding='utf-8') as f:
                json.dump(versions_data, f, indent=2, ensure_ascii=False)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            logger.info(f"更新包创建成功: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            logger.error(f"创建更新包失败: {e}")
            return None
    
    def rollback_update(self, backup_dir: str) -> bool:
        """回滚更新"""
        try:
            if not os.path.exists(backup_dir):
                logger.error(f"备份目录不存在: {backup_dir}")
                return False
            
            logger.info(f"开始回滚更新到: {backup_dir}")
            
            # 恢复备份文件
            for item in os.listdir(backup_dir):
                src = os.path.join(backup_dir, item)
                dst = os.path.join('.', item)
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    logger.debug(f"恢复文件: {item}")
            
            logger.info("更新回滚完成")
            return True
            
        except Exception as e:
            logger.error(f"回滚更新失败: {e}")
            return False
    
    def get_update_history(self) -> List[Dict]:
        """获取更新历史"""
        try:
            versions_file = self.update_dir / "versions.json"
            if versions_file.exists():
                with open(versions_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
                return list(versions_data.get('versions', {}).values())
            return []
        except Exception as e:
            logger.error(f"获取更新历史失败: {e}")
            return []
    
    def cleanup_old_updates(self, keep_count: int = 5) -> bool:
        """清理旧更新"""
        try:
            versions = self.get_update_history()
            if len(versions) <= keep_count:
                return True
            
            # 按版本号排序
            versions.sort(key=lambda x: x['version'], reverse=True)
            
            # 保留最新的几个版本
            versions_to_keep = versions[:keep_count]
            versions_to_delete = versions[keep_count:]
            
            for version_info in versions_to_delete:
                version = version_info['version']
                version_dir = self.update_dir / version
                
                if version_dir.exists():
                    shutil.rmtree(version_dir)
                    logger.info(f"已删除旧版本: {version}")
            
            # 更新versions.json
            versions_file = self.update_dir / "versions.json"
            versions_data = {
                'latest': versions_to_keep[0]['version'] if versions_to_keep else self.current_version,
                'versions': {v['version']: v for v in versions_to_keep}
            }
            
            with open(versions_file, 'w', encoding='utf-8') as f:
                json.dump(versions_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"清理旧更新失败: {e}")
            return False
