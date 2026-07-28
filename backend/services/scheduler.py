"""
定时任务
1. 每日 00:00 更新今日推荐
2. 定时推送（Web Push / 邮件）— MVP 暂不实现推送，保留接口
"""
from apscheduler.schedulers.background import BackgroundScheduler
from services.database import get_conn


def refresh_daily_for_all_users():
    """每天 00:00 为所有用户刷新今日推荐（position 前进一格）"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT user_id FROM daily_queue")
    users = cursor.fetchall()

    for user in users:
        user_id = user["user_id"]
        cursor.execute("""
            SELECT position FROM daily_queue
            WHERE user_id=? AND is_today=1
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            # 没有 is_today，设第一个为 today
            cursor.execute("""
                UPDATE daily_queue SET is_today=1
                WHERE user_id=? AND position=0
            """, (user_id,))
            continue

        next_pos = row["position"] + 1
        cursor.execute("SELECT MAX(position) as max_pos FROM daily_queue WHERE user_id=?", (user_id,))
        max_pos = cursor.fetchone()["max_pos"]

        if next_pos <= max_pos:
            cursor.execute("UPDATE daily_queue SET is_today=0 WHERE user_id=?", (user_id,))
            cursor.execute("""
                UPDATE daily_queue SET is_today=1
                WHERE user_id=? AND position=?
            """, (user_id, next_pos))

    conn.commit()
    conn.close()
    print("[Scheduler] 每日推荐已刷新")


def start_scheduler():
    """启动定时任务"""
    scheduler = BackgroundScheduler()

    # 每天凌晨 00:01 刷新
    scheduler.add_job(
        refresh_daily_for_all_users,
        trigger="cron",
        hour=0,
        minute=1,
        id="daily_refresh",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] 定时任务已启动（每日 00:01 刷新推荐）")
