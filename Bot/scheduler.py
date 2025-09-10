from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ranking import refresh_miners

# Глобальный планировщик
scheduler = AsyncIOScheduler()

def start_scheduler():
    global scheduler
    # Проверяем, не запущен ли уже планировщик
    if not scheduler.running:
        scheduler.add_job(refresh_miners, trigger="interval", hours=12, max_instances=1)
        scheduler.start()
        print(">>> Scheduler started")
    else:
        print(">>> Scheduler already running")
