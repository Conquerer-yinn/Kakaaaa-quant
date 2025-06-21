from backend.schemas.tasks import AcceptedParam, TaskMetadata
from common.config import DAILY_BASICS_FILE


# 当前注册表只维护少量代表任务，让前端和 API 有稳定入口，不做复杂调度平台。
TASK_REGISTRY: dict[str, TaskMetadata] = {
    "daily-basics": TaskMetadata(
        task_name="daily-basics",
        task_type="独立标准任务",
        description="获取每日基础行情数据并追加写入 Excel。",
        accepted_params=[
            AcceptedParam(name="start_date", required=False, description="YYYYMMDD. 首次初始化或手动补数时使用。"),
            AcceptedParam(name="end_date", required=False, description="YYYYMMDD. 默认到今天。"),
            AcceptedParam(name="output_file", required=False, description="自定义输出文件名。"),
        ],
        output_target=DAILY_BASICS_FILE,
    ),
    "market-sentiment": TaskMetadata(
        task_name="market-sentiment",
        task_type="综合研究任务",
        description="增量补充市场情绪历史主表，并同步生成区间补充数据工作簿。",
        accepted_params=[
            AcceptedParam(name="start_date", required=False, description="YYYYMMDD. 手动指定补数起始日期。"),
            AcceptedParam(name="end_date", required=False, description="YYYYMMDD. 默认到今天。"),
            AcceptedParam(name="output_file", required=False, description="可选，手动指定当前历史主表文件名。"),
            AcceptedParam(name="history", required=False, description="默认为 true 更新历史主表；为 false 时生成测试数据工作簿。"),
        ],
        output_target="历史数据主表（按日期区间命名）",
    ),
}



def get_task_metadata(task_name: str) -> TaskMetadata:
    return TASK_REGISTRY[task_name]



def list_task_metadata() -> list[TaskMetadata]:
    return list(TASK_REGISTRY.values())
