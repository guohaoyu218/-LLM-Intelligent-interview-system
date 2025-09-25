"""
AI智能面试官系统启动器
支持多种启动方式：Gradio、Streamlit、FastAPI
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_environment():
    """检查环境配置"""
    print("🔍 检查系统环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 11):
        print("❌ Python版本过低，需要Python 3.11+")
        return False
    
    # 检查.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  未找到.env文件，请复制.env.example为.env并配置")
        example_file = project_root / ".env.example"
        if example_file.exists():
            print(f"   可以执行: cp {example_file} {env_file}")
        return False
    
    # 检查必需的依赖 (包名映射：pip包名 -> Python导入名)
    required_packages = {
        "gradio": "gradio",
        "langchain": "langchain", 
        "sentence-transformers": "sentence_transformers",
        "qdrant-client": "qdrant_client",
        "python-dotenv": "dotenv",
        "fastapi": "fastapi",  # 添加FastAPI检查
        "uvicorn": "uvicorn"   # 添加uvicorn检查
    }
    
    missing_packages = []
    for pip_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("   请执行: pip install -r requirements_new.txt")
        return False
    
    print("✅ 环境检查通过")
    return True

def start_gradio():
    """启动Gradio应用"""
    print("🚀 启动Gradio应用...")
    try:
        from frontend.gradio_app import create_interview_interface
        
        interface = create_interview_interface()
        interface.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"❌ Gradio启动失败: {e}")
        return False

# Streamlit功能已移除，专注于Gradio主界面和FastAPI后端
# 如需数据可视化，可在Gradio界面中集成图表组件

def start_api():
    """启动FastAPI应用"""
    print("🚀 启动FastAPI应用...")
    try:
        import subprocess
        api_file = project_root / "api" / "main.py"
        
        if not api_file.exists():
            print("❌ FastAPI应用文件不存在")
            return False
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app",
            "--host=127.0.0.1",
            "--port=8000",
            "--reload"
        ])
    except Exception as e:
        print(f"❌ FastAPI启动失败: {e}")
        return False

def setup_project():
    """项目初始化设置"""
    print("🔧 项目初始化...")
    
    # 创建必要目录
    directories = [
        "data", "data/resumes", "data/job_descriptions", "data/question_bank",
        "chat_history", "logs", "models", "uploads", "temp"
    ]
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 创建目录: {dir_path}")
    
    # 复制环境变量文件
    env_file = project_root / ".env"
    example_file = project_root / ".env.example"
    
    if not env_file.exists() and example_file.exists():
        import shutil
        shutil.copy(example_file, env_file)
        print(f"   ✅ 创建环境变量文件: {env_file}")
        print("   ⚠️  请编辑.env文件，填入正确的API密钥")
    
    print("✅ 项目初始化完成")

def check_config():
    """检查配置"""
    print("🔍 检查配置...")
    
    try:
        from backend.utils.config import load_config
        config = load_config()
        print("✅ 配置加载成功")
        
        # 检查关键配置
        if not config.get("deepseek", {}).get("api_key"):
            print("⚠️  DeepSeek API Key未配置")
            return False
        
        print("✅ 配置检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI智能面试官系统启动器")
    parser.add_argument(
        "mode", 
        choices=["gradio", "api", "setup", "check"],
        help="启动模式: gradio(主界面) | api(API服务) | setup(初始化) | check(检查配置)"
    )
    parser.add_argument("--skip-check", action="store_true", help="跳过环境检查")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🤖 AI智能面试官系统")
    print("   架构：DeepSeek + BGE + Gradio + FastAPI")  
    print("=" * 60)
    
    # 项目初始化
    if args.mode == "setup":
        setup_project()
        return
    
    # 配置检查
    if args.mode == "check":
        if check_environment() and check_config():
            print("✅ 系统状态正常")
        else:
            print("❌ 系统配置有问题")
        return
    
    # 环境检查
    if not args.skip_check:
        if not check_environment():
            print("\n请先解决环境问题，或使用 --skip-check 跳过检查")
            return
        
        if not check_config():
            print("\n请先解决配置问题，或使用 --skip-check 跳过检查")
            return
    
    # 启动应用
    if args.mode == "gradio":
        start_gradio()
    elif args.mode == "api":
        start_api()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
