from backend.schemas.tasks import DailyBasicsRunRequest, MarketSentimentRunRequest, TaskRunResponse
from backend.services.task_registry import get_task_metadata
from market.jobs.run_daily_basics import run_daily_basics
from market.jobs.run_market_sentiment import run_market_sentiment
from market.services.market_sentiment_workbook import find_latest_history_workbook


def build_task_run_response(metadata, params, output_target, output_path=None, error_message=None) -> TaskRunResponse:
    return TaskRunResponse(
        task_name=metadata.task_name,
        task_type=metadata.task_type,
        description=metadata.description,
        params=params,
        success=output_path is not None and error_message is None,
        output_target=output_target,
        output_path=output_path,
        error_message=error_message,
    )



def run_daily_basics_task(request: DailyBasicsRunRequest) -> TaskRunResponse:
    # 这一层只负责把 API 请求翻译成任务调用，不混入业务指标逻辑。
    metadata = get_task_metadata("daily-basics")
    params = request.model_dump()
    output_target = request.output_file or metadata.output_target

    try:
        output_path = run_daily_basics(
            start_date=request.start_date,
            end_date=request.end_date,
            output_file=output_target,
        )
        return build_task_run_response(
            metadata=metadata,
            params=params,
            output_target=output_target,
            output_path=output_path,
            error_message=None if output_path is not None else "任务未产生新数据或无需更新。",
        )
    except Exception as exc:
        return build_task_run_response(
            metadata=metadata,
            params=params,
            output_target=output_target,
            output_path=None,
            error_message=str(exc),
        )



