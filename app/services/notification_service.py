"""
Serviciu de notificări - Trimitere emailuri și alerte.
"""

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config import EMAIL_USER, EMAIL_PASS, SMTP_SERVER, SMTP_PORT, NOTIFICATION_RECIPIENT
from app.logging_config import get_logger

logger = get_logger("notification_service")


class NotificationService:
    """Serviciu pentru trimiterea de notificări prin email."""
    
    def __init__(self):
        """Inițializează serviciul de notificări."""
        self.user = EMAIL_USER
        self.password = EMAIL_PASS
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.default_recipient = NOTIFICATION_RECIPIENT
        
        logger.info(f"⚙️  NotificationService inițializat pentru {self.user}")
    
    def send_notification(self, subject: str, content: str, recipient: Optional[str] = None) -> bool:
        """
        Trimite un email de notificare.
        
        Args:
            subject: Subiectul emailului
            content: Conținutul emailului
            recipient: Destinatarul (opțional, folosește default din config)
            
        Returns:
            True dacă emailul a fost trimis cu succes, False altfel
        """
        target_recipient = recipient or self.default_recipient
        
        if not target_recipient:
            logger.error("Niciun destinatar specificat pentru notificare")
            return False
        
        logger.info(f"📤 Trimitere notificare către {target_recipient}...")
        
        try:
            msg = EmailMessage()
            msg['From'] = f'Automatizare comenzi Eeatingh <{self.user}>'
            msg['To'] = target_recipient
            msg['Subject'] = f'🔔 {subject}'
            msg.set_content(content)
            
            with smtplib.SMTP(host=self.smtp_server, port=self.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.user, self.password)
                smtp.send_message(msg)
            
            logger.info(f"✅ Email trimis cu succes către {target_recipient}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Eroare la trimiterea emailului: {e}", exc_info=True)
            return False
    
    def send_error_notification(self, error_message: str, context: str = "") -> bool:
        """
        Trimite o notificare de eroare.
        
        Args:
            error_message: Mesajul de eroare
            context: Context suplimentar (opțional)
            
        Returns:
            True dacă notificarea a fost trimisă cu succes
        """
        subject = "Eroare în aplicația Eeatingh"
        context_text = f"Context: {context}\n" if context else ""
        content = f"""
A apărut o eroare în aplicația de automatizare comenzi Eeatingh.

Eroare: {error_message}

{context_text}
Vă rugăm verificați log-urile pentru mai multe detalii.
"""
        return self.send_notification(subject, content)
    
    def send_order_notification(self, order_id: str, order_details: str = "") -> bool:
        """
        Trimite o notificare pentru o comandă nouă.
        
        Args:
            order_id: ID-ul comenzii
            order_details: Detalii despre comandă (opțional)
            
        Returns:
            True dacă notificarea a fost trimisă cu succes
        """
        subject = f"Comandă nouă #{order_id}"
        details_text = f"\n\nDetalii:\n{order_details}" if order_details else ""
        content = f"""
O comandă nouă a fost procesată cu succes!

ID Comandă: #{order_id}{details_text}

Comandă disponibilă pentru preluare în sistem.
"""
        return self.send_notification(subject, content)
