import sys
import os

print("=" * 60)
print("PYTHON 环境诊断开始")
print("=" * 60)

# 1. 打印当前使用的 Python 解释器路径
print(f"[*] 当前 Python 解释器: {sys.executable}\n")

try:
    # 2. 导入 deepface 并打印其版本和安装位置
    import deepface

    print("[+] 'import deepface' 成功！")
    print(f"    - 版本 (deepface.__version__): {deepface.__version__}")

    # __file__ 属性指向包的 __init__.py 文件
    package_init_file = deepface.__file__
    print(f"    - 安装位置 (deepface.__file__): {package_init_file}")

    # 3. 探查 deepface 包的目录结构
    package_directory = os.path.dirname(package_init_file)
    print(f"\n[*] 探查 deepface 包的目录: {package_directory}")

    # 列出目录下的所有文件和文件夹
    try:
        dir_contents = os.listdir(package_directory)
        print("    - 目录内容:")
        for item in sorted(dir_contents):
            item_path = os.path.join(package_directory, item)
            if os.path.isdir(item_path):
                print(f"        [文件夹] {item}")
            else:
                print(f"        [文件]   {item}")
    except Exception as e:
        print(f"    - [错误] 无法读取目录内容: {e}")

    # 4. 尝试所有可能的导入路径
    print("\n[*] 尝试不同的导入路径...")

    # 尝试最新版本的路径
    try:
        from deepface.modules import distance

        print("    - ✅ 成功: from deepface.modules import distance")
    except (ModuleNotFoundError, ImportError) as e:
        print(f"    - ❌ 失败: from deepface.modules import distance. 错误: {e}")

    # 尝试旧版本的路径
    try:
        from deepface.commons import distance

        print("    - ✅ 成功: from deepface.commons import distance")
    except (ModuleNotFoundError, ImportError) as e:
        print(f"    - ❌ 失败: from deepface.commons import distance. 错误: {e}")

    # 尝试另一个可能的新版本路径
    try:
        from deepface import distance

        print("    - ✅ 成功: from deepface import distance")
    except (ModuleNotFoundError, ImportError) as e:
        print(f"    - ❌ 失败: from deepface import distance. 错误: {e}")

except Exception as e:
    print(f"\n\n[!!!] 关键错误: 连 'import deepface' 都失败了！错误信息: {e}")

print("=" * 60)
print("诊断结束")
print("=" * 60)