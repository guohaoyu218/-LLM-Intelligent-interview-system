"""
FastAPI主应用
AI智能面试官系统API服务
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.utils.config import load_config
from backend.utils.logger import get_logger
from backend.services.interview_service import InterviewService
from backend.services.evaluation_service import EvaluationService
from backend.services.report_service import ReportService

# 全局变量
app = FastAPI(
    title="AI智能面试官系统API",
    description="基于DeepSeek的智能面试评估系统",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
config = None
logger = None
interview_service = None
evaluation_service = None
report_service = None

# 内存存储（生产环境应使用数据库）
active_sessions: Dict[str, Dict[str, Any]] = {}


# Pydantic模型
class InterviewStartRequest(BaseModel):
    mode: str = Field(..., description="面试模式", regex="^(basic|jd_based|resume_based)$")
    resume_content: Optional[str] = Field(None, description="简历内容")
    jd_content: Optional[str] = Field(None, description="职位描述内容")


class InterviewContinueRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    user_response: str = Field(..., description="用户回答")


class InterviewEndRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")


class ApiResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    message: Optional[str] = Field(None, description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


# 依赖注入
async def get_services():
    """获取服务实例"""
    global config, logger, interview_service, evaluation_service, report_service
    
    if not config:
        try:
            config = load_config()
            logger = get_logger(__name__)
            interview_service = InterviewService(config)
            evaluation_service = EvaluationService(config)
            report_service = ReportService(config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"服务初始化失败: {str(e)}")
    
    return {
        "config": config,
        "logger": logger,
        "interview_service": interview_service,
        "evaluation_service": evaluation_service,
        "report_service": report_service
    }


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await get_services()
    print("🚀 AI智能面试官API服务已启动")


# 健康检查
@app.get("/health", response_model=ApiResponse)
async def health_check():
    """健康检查接口"""
    return ApiResponse(
        status="success",
        message="服务运行正常",
        data={
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(active_sessions)
        }
    )


# 系统信息
@app.get("/info", response_model=ApiResponse)
async def get_system_info(services = Depends(get_services)):
    """获取系统信息"""
    try:
        return ApiResponse(
            status="success",
            message="系统信息获取成功",
            data={
                "name": "AI智能面试官系统",
                "version": "1.0.0",
                "description": "基于DeepSeek的智能面试评估系统",
                "active_sessions": len(active_sessions),
                "supported_modes": ["basic", "jd_based", "resume_based"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 开始面试
@app.post("/interview/start", response_model=ApiResponse)
async def start_interview(
    request: InterviewStartRequest,
    services = Depends(get_services)
):
    """开始面试"""
    try:
        logger = services["logger"]
        interview_service = services["interview_service"]
        
        # 启动面试
        result = interview_service.start_interview(
            request.mode, 
            request.resume_content or "", 
            request.jd_content or ""
        )
        
        if result.get('status') == 'success':
            session_id = result['session_id']
            
            # 创建会话数据
            session_data = {
                'session_id': session_id,
                'mode': request.mode,
                'start_time': datetime.now().isoformat(),
                'status': 'active',
                'conversation_history': [
                    {
                        'role': 'assistant',
                        'content': result['welcome_message'],
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'metadata': {
                    'resume_content': request.resume_content or '',
                    'jd_content': request.jd_content or ''
                }
            }
            
            # 保存到内存
            active_sessions[session_id] = session_data
            
            logger.info(f"面试会话已创建: {session_id}")
            
            return ApiResponse(
                status="success",
                message="面试已开始",
                data={
                    "session_id": session_id,
                    "welcome_message": result['welcome_message']
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result.get('message', '面试启动失败'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 继续面试
@app.post("/interview/continue", response_model=ApiResponse)
async def continue_interview(
    request: InterviewContinueRequest,
    services = Depends(get_services)
):
    """继续面试对话"""
    try:
        logger = services["logger"]
        interview_service = services["interview_service"]
        
        # 检查会话是否存在
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="面试会话不存在")
        
        session_data = active_sessions[request.session_id]
        
        # 检查会话状态
        if session_data.get('status') != 'active':
            raise HTTPException(status_code=400, detail="面试会话已结束")
        
        # 继续面试
        result = interview_service.continue_interview(
            request.session_id,
            request.user_response,
            session_data
        )
        
        if result.get('status') == 'success':
            # 更新会话数据
            active_sessions[request.session_id] = session_data
            
            return ApiResponse(
                status="success",
                message="回应生成成功",
                data={
                    "session_id": request.session_id,
                    "interviewer_response": result['interviewer_response'],
                    "should_end": result.get('should_end', False),
                    "question_count": session_data['metadata'].get('question_count', 0)
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result.get('message', '回应生成失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 结束面试
@app.post("/interview/end", response_model=ApiResponse)
async def end_interview(
    request: InterviewEndRequest,
    background_tasks: BackgroundTasks,
    services = Depends(get_services)
):
    """结束面试并生成评估"""
    try:
        logger = services["logger"]
        evaluation_service = services["evaluation_service"]
        report_service = services["report_service"]
        
        # 检查会话是否存在
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="面试会话不存在")
        
        session_data = active_sessions[request.session_id]
        
        # 更新会话状态
        session_data['end_time'] = datetime.now().isoformat()
        session_data['status'] = 'completed'
        
        # 后台任务：生成评估和报告
        background_tasks.add_task(
            generate_evaluation_and_report,
            request.session_id,
            session_data,
            evaluation_service,
            report_service
        )
        
        logger.info(f"面试会话已结束: {request.session_id}")
        
        return ApiResponse(
            status="success",
            message="面试已结束，评估报告正在生成中",
            data={
                "session_id": request.session_id,
                "conversation_count": len(session_data.get('conversation_history', [])),
                "duration_minutes": _calculate_duration(session_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 获取面试状态
@app.get("/interview/status/{session_id}", response_model=ApiResponse)
async def get_interview_status(session_id: str):
    """获取面试状态"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="面试会话不存在")
        
        session_data = active_sessions[session_id]
        
        return ApiResponse(
            status="success",
            message="状态获取成功",
            data={
                "session_id": session_id,
                "status": session_data.get('status'),
                "mode": session_data.get('mode'),
                "start_time": session_data.get('start_time'),
                "end_time": session_data.get('end_time'),
                "question_count": len([msg for msg in session_data.get('conversation_history', []) if msg['role'] == 'user']),
                "total_messages": len(session_data.get('conversation_history', []))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 获取面试历史
@app.get("/interview/history/{session_id}", response_model=ApiResponse)
async def get_interview_history(session_id: str):
    """获取面试对话历史"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="面试会话不存在")
        
        session_data = active_sessions[session_id]
        
        return ApiResponse(
            status="success",
            message="历史获取成功",
            data={
                "session_id": session_id,
                "conversation_history": session_data.get('conversation_history', [])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 获取评估结果
@app.get("/evaluation/{session_id}", response_model=ApiResponse)
async def get_evaluation_result(session_id: str):
    """获取面试评估结果"""
    try:
        # 这里应该从数据库或缓存中获取评估结果
        # 简化版本直接从内存中查找
        
        evaluation_result = None
        # 在实际项目中，这里应该查询数据库
        
        if not evaluation_result:
            raise HTTPException(status_code=404, detail="评估结果不存在或正在生成中")
        
        return ApiResponse(
            status="success",
            message="评估结果获取成功",
            data=evaluation_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 获取会话列表
@app.get("/sessions", response_model=ApiResponse)
async def get_active_sessions():
    """获取活跃会话列表"""
    try:
        sessions_info = []
        
        for session_id, session_data in active_sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "mode": session_data.get('mode'),
                "status": session_data.get('status'),
                "start_time": session_data.get('start_time'),
                "question_count": len([msg for msg in session_data.get('conversation_history', []) if msg['role'] == 'user'])
            })
        
        return ApiResponse(
            status="success",
            message="会话列表获取成功",
            data={
                "total_sessions": len(sessions_info),
                "sessions": sessions_info
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 辅助函数
async def generate_evaluation_and_report(
    session_id: str,
    session_data: Dict[str, Any],
    evaluation_service: EvaluationService,
    report_service: ReportService
):
    """后台生成评估和报告"""
    try:
        # 生成评估
        evaluation_result = evaluation_service.evaluate_interview(session_data)
        
        # 生成报告
        report_result = report_service.generate_interview_report(
            session_data, evaluation_result, "markdown"
        )
        
        # 保存结果（在实际项目中应该保存到数据库）
        session_data['evaluation_result'] = evaluation_result
        session_data['report_result'] = report_result
        
        print(f"评估和报告生成完成: {session_id}")
        
    except Exception as e:
        print(f"生成评估和报告失败 {session_id}: {e}")


def _calculate_duration(session_data: Dict[str, Any]) -> int:
    """计算面试时长（分钟）"""
    try:
        start_time = datetime.fromisoformat(session_data['start_time'])
        end_time = datetime.fromisoformat(session_data.get('end_time', datetime.now().isoformat()))
        duration_seconds = (end_time - start_time).total_seconds()
        return int(duration_seconds / 60)
    except:
        return 0


# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error", 
            "message": f"内部服务器错误: {str(exc)}",
            "data": None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
