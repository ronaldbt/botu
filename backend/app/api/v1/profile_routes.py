# backend/app/api/v1/profile_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.core.auth import get_current_user
from app.db.models import User
from app.db import crud_users

router = APIRouter(prefix="/users", tags=["profile"])

# Pydantic models
class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    subscription_plan: str
    subscription_status: str
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None

class SubscriptionChangeRequest(BaseModel):
    plan: str  # 'free', 'basic', 'premium'

class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None

class PaymentHistoryResponse(BaseModel):
    id: int
    date: datetime
    plan: str
    amount: float
    status: str
    paypal_id: Optional[str] = None

@router.get("/profile", response_model=ProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el perfil completo del usuario actual"""
    try:
        return ProfileResponse(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name,
            email=current_user.email,
            phone=current_user.phone,
            country=current_user.country,
            is_admin=current_user.is_admin,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            subscription_plan=current_user.subscription_plan or 'inactive',
            subscription_status=current_user.subscription_status or 'inactive',
            subscription_start_date=current_user.subscription_start_date,
            subscription_end_date=current_user.subscription_end_date,
            last_payment_date=current_user.last_payment_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo perfil: {str(e)}"
        )

@router.put("/profile", response_model=ProfileResponse)
async def update_user_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza el perfil del usuario actual"""
    try:
        # Actualizar solo los campos proporcionados
        update_data = profile_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        # Actualizar last_activity
        current_user.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(current_user)
        
        return ProfileResponse(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name,
            email=current_user.email,
            phone=current_user.phone,
            country=current_user.country,
            is_admin=current_user.is_admin,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            subscription_plan=current_user.subscription_plan or 'inactive',
            subscription_status=current_user.subscription_status or 'inactive',
            subscription_start_date=current_user.subscription_start_date,
            subscription_end_date=current_user.subscription_end_date,
            last_payment_date=current_user.last_payment_date
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando perfil: {str(e)}"
        )

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_user_subscription(
    current_user: User = Depends(get_current_user)
):
    """Obtiene la información de suscripción del usuario actual"""
    try:
        return SubscriptionResponse(
            plan=current_user.subscription_plan or 'free',
            status=current_user.subscription_status or 'inactive',
            start_date=current_user.subscription_start_date,
            end_date=current_user.subscription_end_date,
            last_payment_date=current_user.last_payment_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo suscripción: {str(e)}"
        )

@router.post("/subscription/change", response_model=SubscriptionResponse)
async def change_subscription_plan(
    request: SubscriptionChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambia el plan de suscripción del usuario (solo para downgrades a free)"""
    try:
        valid_plans = ['inactive', 'alerts', 'trading']
        if request.plan not in valid_plans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan de suscripción inválido"
            )
        
        # Solo permitir cambio a 'inactive', otros planes requieren pago/contacto
        if request.plan != 'inactive':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para activar planes de pago, contacta al administrador"
            )
        
        # Cambiar a plan inactivo (cancelar suscripción)
        current_user.subscription_plan = 'inactive'
        current_user.subscription_status = 'inactive'
        current_user.subscription_end_date = datetime.utcnow()
        current_user.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(current_user)
        
        return SubscriptionResponse(
            plan=current_user.subscription_plan,
            status=current_user.subscription_status,
            start_date=current_user.subscription_start_date,
            end_date=current_user.subscription_end_date,
            last_payment_date=current_user.last_payment_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cambiando plan: {str(e)}"
        )

@router.get("/payments")
async def get_payment_history(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el historial de pagos del usuario"""
    try:
        # Por ahora retornamos un historial vacío
        # En el futuro esto se conectaría con una tabla de pagos real
        payment_history = []
        
        # Si el usuario tiene pagos, aquí estarían
        if current_user.last_payment_date and current_user.subscription_plan != 'inactive':
            amount = 20 if current_user.subscription_plan == 'alerts' else 0
            payment_history.append({
                "id": 1,
                "date": current_user.last_payment_date,
                "plan": current_user.subscription_plan,
                "amount": amount,
                "status": "Completado",
                "paypal_id": current_user.paypal_subscription_id or "N/A"
            })
        
        return payment_history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial de pagos: {str(e)}"
        )

@router.post("/subscription/webhook")
async def paypal_webhook(
    # Este endpoint será llamado por PayPal cuando se complete un pago
    # Por simplicidad, no implementamos la verificación completa de PayPal aquí
    db: Session = Depends(get_db)
):
    """Webhook para procesar pagos de PayPal"""
    try:
        # En una implementación real, aquí:
        # 1. Verificarías la firma de PayPal
        # 2. Procesarías el evento de pago
        # 3. Actualizarías la suscripción del usuario
        # 4. Enviarías emails de confirmación
        
        return {"message": "Webhook procesado correctamente"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando webhook: {str(e)}"
        )