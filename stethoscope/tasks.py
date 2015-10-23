from celery.task import Task
from celery.registry import tasks

class MyTask(Task):
    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Did something.")
tasks.register(MyTask)
