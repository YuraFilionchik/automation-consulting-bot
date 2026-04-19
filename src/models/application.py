"""Модель заявки"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

from src.models.database import get_db_connection
from src.utils.formatters import sanitize_html


@dataclass
class Application:
    """Модель заявки"""
    
    id: Optional[int] = None
    user_id: Optional[int] = None
    status: str = "new"
    project_type: Optional[str] = None
    project_subtype: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    contact_info: Optional[str] = None
    task_description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return asdict(self)
    
    def format_for_admin(self):
        """Format for admin notification"""
        text = f"📨 <b>New Application #{self.id}</b>\n\n"
        text += f"📋 <b>Type:</b> {sanitize_html(self.project_type or 'Not specified')}"
        if self.project_subtype:
            text += f" ({sanitize_html(self.project_subtype)})"
        text += f"\n"
        text += f"💰 <b>Budget:</b> {self.budget_range or 'Not specified'}\n"
        text += f"⏰ <b>Timeline:</b> {self.timeline or 'Not specified'}\n"
        text += f"📞 <b>Contact:</b> {sanitize_html(self.contact_info or 'Not specified')}\n"
        text += f"📝 <b>Task:</b> {sanitize_html(self.task_description or 'Not described')}\n\n"
        text += f"👤 <b>User:</b> {self.user_id}\n"
        text += f"🕐 <b>Time:</b> {self.created_at}"
        
        return text
    
    def format_for_user(self):
        """Format for user confirmation"""
        text = f"✅ <b>Application submitted!</b>\n\n"
        text += f"📋 <b>Summary:</b>\n"
        text += f"Type: {sanitize_html(self.project_type or 'Not specified')}\n"
        if self.project_subtype:
            text += f"Subtype: {sanitize_html(self.project_subtype)}\n"
        text += f"Budget: {self.budget_range or 'Not specified'}\n"
        text += f"Timeline: {self.timeline or 'Not specified'}\n"
        text += f"Contact: {sanitize_html(self.contact_info or 'Not specified')}\n"
        text += f"Task: {sanitize_html(self.task_description or 'Not described')}\n\n"
        text += f"Our manager will contact you shortly! ⏳"
        
        return text


async def save_application(app_data: dict) -> Application:
    """Сохранить заявку в БД"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications 
                (user_id, project_type, project_subtype, budget_range, 
                 timeline, contact_info, task_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            app_data.get('user_id'),
            app_data.get('project_type'),
            app_data.get('project_subtype'),
            app_data.get('budget_range'),
            app_data.get('timeline'),
            app_data.get('contact_info'),
            app_data.get('task_description')
        ))
        
        app_id = cursor.lastrowid
        
        # Получить сохраненную заявку
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        
        return Application(**dict(row))


async def get_application(app_id: int) -> Optional[Application]:
    """Получить заявку по ID"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        
        if row:
            return Application(**dict(row))
        return None


async def get_user_applications(user_id: int) -> list:
    """Получить все заявки пользователя"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM applications WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        
        return [Application(**dict(row)) for row in rows]
