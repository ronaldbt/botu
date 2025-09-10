# backend/app/api/v1/health_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.db.database import get_db
from app.core.auth import get_current_user
from app.db.models import User
from app.services.health_monitor_service import health_monitor

router = APIRouter()

@router.get("/health/status")
async def get_health_status(current_user: User = Depends(get_current_user)):
    """Obtiene el estado actual del Health Monitor"""
    try:
        # Solo admins pueden ver el estado completo de salud
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden ver el estado de salud del sistema"
            )
        
        # Obtener estado del health monitor
        monitor_status = health_monitor.get_status()
        
        # Información adicional del sistema
        system_info = {
            "current_time": datetime.now().isoformat(),
            "monitor_running": monitor_status['is_running'],
            "last_report": monitor_status['last_report_sent'],
            "recent_alerts": monitor_status['recent_alerts'],
            "next_reports": monitor_status['next_report_times'],
            "config": monitor_status['config']
        }
        
        return {
            "success": True,
            "health_monitor": system_info,
            "message": "Health Monitor operativo" if monitor_status['is_running'] else "Health Monitor detenido"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estado de salud: {str(e)}"
        )

@router.post("/health/start")
async def start_health_monitor(current_user: User = Depends(get_current_user)):
    """Inicia el Health Monitor manualmente"""
    try:
        # Solo admins pueden controlar el health monitor
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden controlar el Health Monitor"
            )
        
        if health_monitor.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Health Monitor ya está ejecutándose"
            )
        
        # Iniciar health monitor
        success = await health_monitor.start_monitoring()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error iniciando Health Monitor"
            )
        
        return {
            "success": True,
            "message": "Health Monitor iniciado exitosamente",
            "started_by": current_user.username,
            "start_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error iniciando Health Monitor: {str(e)}"
        )

@router.post("/health/stop")
async def stop_health_monitor(current_user: User = Depends(get_current_user)):
    """Detiene el Health Monitor manualmente"""
    try:
        # Solo admins pueden controlar el health monitor
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden controlar el Health Monitor"
            )
        
        if not health_monitor.is_running:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health Monitor no está ejecutándose"
            )
        
        # Detener health monitor
        success = await health_monitor.stop_monitoring()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deteniendo Health Monitor"
            )
        
        return {
            "success": True,
            "message": "Health Monitor detenido exitosamente",
            "stopped_by": current_user.username,
            "stop_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deteniendo Health Monitor: {str(e)}"
        )

@router.get("/health/report")
async def get_health_report(current_user: User = Depends(get_current_user)):
    """Genera y obtiene un reporte completo de salud del sistema"""
    try:
        # Solo admins pueden ver reportes de salud
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden ver reportes de salud"
            )
        
        # Generar reporte de salud en tiempo real
        health_data = {
            "server": await health_monitor._check_server_health(),
            "database": await health_monitor._check_database_health(),
            "scanners": await health_monitor._check_scanners_health(),
            "binance_api": await health_monitor._check_binance_api_health()
        }
        
        # Estadísticas de alertas recientes
        recent_alerts_24h = len([a for a in health_monitor.system_alerts 
                               if (datetime.now() - datetime.fromisoformat(a['timestamp'])).total_seconds() < 24 * 3600])
        
        recent_alerts_1h = len([a for a in health_monitor.system_alerts 
                              if (datetime.now() - datetime.fromisoformat(a['timestamp'])).total_seconds() < 3600])
        
        # Estado general del sistema
        overall_healthy = all([
            health_data['server']['healthy'],
            health_data['database']['healthy'],
            health_data['scanners']['healthy'],
            health_data['binance_api']['healthy']
        ])
        
        return {
            "success": True,
            "report_time": datetime.now().isoformat(),
            "overall_healthy": overall_healthy,
            "components": health_data,
            "alerts_stats": {
                "last_24h": recent_alerts_24h,
                "last_1h": recent_alerts_1h,
                "recent_alerts": health_monitor.system_alerts[-10:]  # Últimas 10 alertas
            },
            "monitor_status": health_monitor.get_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte de salud: {str(e)}"
        )

@router.post("/health/test-alert")
async def test_health_alert(current_user: User = Depends(get_current_user)):
    """Envía una alerta de prueba para verificar el sistema de notificaciones"""
    try:
        # Solo admins pueden enviar alertas de prueba
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden enviar alertas de prueba"
            )
        
        # Crear alerta de prueba
        test_message = f"""🧪 **ALERTA DE PRUEBA**
📅 {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}
👤 Enviada por: {current_user.username}

✅ Sistema de alertas funcionando correctamente
🏥 Health Monitor operativo
📡 Conexión Telegram activa

Esta es una prueba del sistema de notificaciones de salud."""

        # Enviar mensaje de prueba
        await health_monitor._send_admin_telegram_message(test_message)
        
        return {
            "success": True,
            "message": "Alerta de prueba enviada exitosamente",
            "sent_by": current_user.username,
            "sent_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando alerta de prueba: {str(e)}"
        )