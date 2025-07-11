#!/usr/bin/env python3
# add_employees.py

import os
import sys
import argparse

import face_recognition
import numpy as np

from app import create_app, db
from app.models.employee import Employee
from app.models.user import User, RoleEnum

def extract_face_encoding(image_path: str) -> np.ndarray:
    """
    加载一张人脸图片文件，检测并返回第一个人脸的 128D 编码向量。
    抛出 ValueError 如果未检测到人脸或图片加载失败。
    """
    image = face_recognition.load_image_file(image_path)
    encs = face_recognition.face_encodings(image)
    if not encs:
        raise ValueError(f"No face found in image: {image_path}")
    return encs[0]

def add_employee(name: str, image_path: str):
    """
    1. 创建或获取 User 实例
    2. 如果不存在对应的 Employee，再提取人脸编码并保存，同时关联 user_id
    """
    # —— 1. 构造或获取 User —— 
    user = User.query.filter_by(username=name).first()
    if not user:
        user = User(
            username=name,
            email=f"{name}@example.com",
            role=RoleEnum.USER
        )
        user.set_password("123456")
        db.session.add(user)
        db.session.flush()  # 确保 user.id 可用
        print(f"[USER] Created User '{user.username}' (id={user.id})")
    else:
        print(f"[USER] User '{user.username}' already exists (id={user.id})")

    # —— 2. 创建 Employee 并关联到上面 User —— 
    exists = Employee.query.filter_by(name=name).first()
    if exists:
        print(f"[SKIP] Employee '{name}' already exists (id={exists.id})")
        return

    encoding = extract_face_encoding(image_path)
    encoding_bytes = encoding.tobytes()
    emp = Employee(
        name=name,
        face_encoding=encoding_bytes,
        user_id=user.id
    )
    db.session.add(emp)
    print(f"[ADD] Employee '{name}' ← {os.path.basename(image_path)} (user_id={user.id})")

def main():
    parser = argparse.ArgumentParser(description="批量或单条添加 Employee 数据（并关联 User）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dir", "-d",
        help="批量模式：指定一个目录，遍历其中所有 .jpg/.jpeg/.png 文件，文件名（去扩展名）作为员工姓名"
    )
    group.add_argument(
        "--name", "-n", nargs=2, metavar=("NAME", "IMG"),
        help="单条模式：--name '张三' path/to/zhangsan.jpg"
    )
    args = parser.parse_args()

    # 初始化 Flask 应用上下文
    app = create_app()
    with app.app_context():
        if args.dir:
            directory = args.dir
            if not os.path.isdir(directory):
                print(f"Error: 目录不存在: {directory}", file=sys.stderr)
                sys.exit(1)
            for fn in os.listdir(directory):
                if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                name = os.path.splitext(fn)[0]
                img_path = os.path.join(directory, fn)
                try:
                    add_employee(name, img_path)
                except Exception as e:
                    print(f"[FAIL] {fn}: {e}", file=sys.stderr)
            db.session.commit()
            print("批量添加完成。")
        else:
            name, img = args.name
            if not os.path.isfile(img):
                print(f"Error: 文件不存在: {img}", file=sys.stderr)
                sys.exit(1)
            try:
                add_employee(name, img)
                db.session.commit()
                print("单条添加完成。")
            except Exception as e:
                print(f"[FAIL] {name}: {e}", file=sys.stderr)
                sys.exit(1)

if __name__ == "__main__":
    main()


# #!/usr/bin/env python3
# # add_employees.py

# import os
# import sys
# import argparse

# import face_recognition
# import numpy as np

# from app import create_app, db
# from app.models.employee import Employee

# def extract_face_encoding(image_path: str) -> np.ndarray:
#     """
#     加载一张人脸图片文件，检测并返回第一个人脸的 128D 编码向量。
#     抛出 ValueError 如果未检测到人脸或图片加载失败。
#     """
#     image = face_recognition.load_image_file(image_path)
#     encs = face_recognition.face_encodings(image)
#     if not encs:
#         raise ValueError(f"No face found in image: {image_path}")
#     return encs[0]

# def add_employee(name: str, image_path: str):
#     """
#     提取 image_path 中的 face_encoding，
#     并以 name 创建一个 Employee 记录到数据库。
#     """
#     # 提取编码
#     encoding = extract_face_encoding(image_path)
#     # 转为 bytes 存储
#     encoding_bytes = encoding.tobytes()

#     # 检查是否已存在
#     exists = Employee.query.filter_by(name=name).first()
#     if exists:
#         print(f"[SKIP] Employee '{name}' already exists (id={exists.id})")
#         return

#     emp = Employee(name=name, face_encoding=encoding_bytes)
#     db.session.add(emp)
#     print(f"[ADD] {name} ← {os.path.basename(image_path)}")

# def main():
#     parser = argparse.ArgumentParser(description="批量或单条添加 Employee 数据")
#     group = parser.add_mutually_exclusive_group(required=True)
#     group.add_argument(
#         "--dir", "-d",
#         help="批量模式：指定一个目录，脚本会遍历其中所有 .jpg/.png 文件，文件名（去扩展名）作为员工姓名"
#     )
#     group.add_argument(
#         "--name", "-n", nargs=2, metavar=("NAME", "IMG"),
#         help="单条模式：--name '张三' path/to/zhangsan.jpg"
#     )
#     args = parser.parse_args()

#     # 初始化 Flask 应用上下文
#     app = create_app()  
#     with app.app_context():
#         if args.dir:
#             directory = args.dir
#             if not os.path.isdir(directory):
#                 print(f"Error: 目录不存在: {directory}", file=sys.stderr)
#                 sys.exit(1)
#             for fn in os.listdir(directory):
#                 if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
#                     continue
#                 name = os.path.splitext(fn)[0]
#                 img_path = os.path.join(directory, fn)
#                 try:
#                     add_employee(name, img_path)
#                 except Exception as e:
#                     print(f"[FAIL] {fn}: {e}", file=sys.stderr)
#             db.session.commit()
#             print("批量添加完成。")
#         else:
#             name, img = args.name
#             if not os.path.isfile(img):
#                 print(f"Error: 文件不存在: {img}", file=sys.stderr)
#                 sys.exit(1)
#             try:
#                 add_employee(name, img)
#                 db.session.commit()
#                 print("单条添加完成。")
#             except Exception as e:
#                 print(f"[FAIL] {name}: {e}", file=sys.stderr)
#                 sys.exit(1)

# if __name__ == "__main__":
#     main()
