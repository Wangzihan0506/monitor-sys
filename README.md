环境配置好后的终端启动流程：
```
config.ini文件里修改成自己数据库密码账号
```
cd 到项目backend文件夹，输入  
```    
conda activate flask-py310
```
python app.py
```
此时后端已经运行
```
cd到frontend文件夹 
```
第一次的话输入 pnpm install之后就不用了   
```
pnpm run serve
```
此时前端启动 复制第一行网址到浏览器打开即可进入注册登陆页面
