## 启动
后端：
cd backend

conda activate vision

python main.py

前端：
在frontend/apps/web-naive中开发

cd frontend

pnpm run dev 

选择robot/web-naive

## TODO
1. 标题改为智慧校园
2. 改为多机器人
  - 涉及巡检任务、实时监控
3. 巡检点位：
  - 增删改
  - 地图（人工标点、确定数据格式）
4. 巡检任务：
  - 增删改
  - 改为每个任务执行多个点位的巡检（可选择某个空闲机器人）
  - 巡检人员设置为添加该任务的登录用户
5. 修改告警数据页面
  - 消防通道        图片        时间
  - 停车场          图片        时间
  - 听河池栏杆损坏  图片        时间
  - 乱扔垃圾        图片        时间
6. 新增机器人控制页面
  - 选择某个机器人
  - 运动控制
  - 位置校准
  - 设置目标点（仿rviz）
  - RGB视频流
  - 地图、机器人实时位置
