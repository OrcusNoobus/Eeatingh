"""
Email Listener cu IMAP IDLE - Monitoring în timp real pentru emailuri noi.
Include funcționalitate integrată de curățare automată a emailurilor vechi.
"""

from imapclient import IMAPClient
import email
import time
from datetime import datetime, timedelta
from typing import Optional

from app.config import (
    EMAIL_USER, EMAIL_PASS, IMAP_SERVER, IDLE_TIMEOUT, EMAIL_SENDER,
    CLEANUP_THRESHOLD, CLEANUP_DAYS_OLD, ORDER_COUNTER_FILE
)
from app.logging_config import get_logger
from app.services.order_service import parse_order_html, save_order_json, is_order_processed
from app.services.notification_service import NotificationService

logger = get_logger("email_listener")


class EmailListener:
    """
    Clasa pentru monitoring continuu emailuri folosind IMAP IDLE.
    Procesează automat emailurile noi în timp real și curăță emailurile vechi.
    """
    
    def __init__(self):
        """Inițializare EmailListener cu credențiale din config."""
        self.user = EMAIL_USER
        self.password = EMAIL_PASS
        self.imap_server = IMAP_SERVER
        self.mail: Optional[IMAPClient] = None
        self.running = True
        self.idle_timeout = IDLE_TIMEOUT
        
        logger.info(f"⚙️  EmailListener inițializat pentru {self.user}")
    
    def connect(self) -> bool:
        """Conectare la serverul IMAP."""
        try:
            logger.info("🔌 Conectare la serverul IMAP...")
            self.mail = IMAPClient(self.imap_server, ssl=True, timeout=30)
            self.mail.login(self.user, self.password)
            self.mail.select_folder('INBOX')
            logger.info("✅ Conectat cu succes la IMAP")
            return True
        except Exception as e:
            logger.error(f"❌ Eroare la conectare IMAP: {e}")
            self.mail = None
            return False
    
    def disconnect(self):
        """Deconectare de la serverul IMAP."""
        try:
            if self.mail:
                self.mail.logout()
                logger.info("🔌 Deconectat de la IMAP")
        except:
            pass
        finally:
            self.mail = None
    
    def increment_order_counter(self) -> int:
        """
        Incrementează contorul de comenzi procesate și returnează valoarea.
        
        Returns:
            Numărul curent de comenzi procesate
        """
        try:
            if ORDER_COUNTER_FILE.exists():
                with open(ORDER_COUNTER_FILE, 'r') as f:
                    count = int(f.read().strip())
            else:
                count = 0
            
            count += 1
            
            with open(ORDER_COUNTER_FILE, 'w') as f:
                f.write(str(count))
            
            return count
        except Exception as e:
            logger.error(f"Eroare la incrementarea contorului: {e}")
            return 0
    
    def reset_order_counter(self):
        """Resetează contorul de comenzi la 0."""
        try:
            with open(ORDER_COUNTER_FILE, 'w') as f:
                f.write('0')
            logger.info("🔄 Contor resetat la 0")
        except Exception as e:
            logger.error(f"Eroare la resetarea contorului: {e}")
    
    def cleanup_old_emails(self, days_old: int = CLEANUP_DAYS_OLD):
        """
        Șterge emailurile mai vechi de X zile din inbox.
        Folosește conexiunea IMAP existentă.
        
        Args:
            days_old: Numărul de zile (emailuri mai vechi vor fi șterse)
        """
        if not self.mail:
            logger.error("Nu există conexiune IMAP activă pentru cleanup")
            return
        
        try:
            logger.info(f"🧹 Pornire curățare emailuri mai vechi de {days_old} zile...")
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_date_str = cutoff_date.strftime("%d-%b-%Y")
            
            # Caută emailuri de la eeatingh mai vechi de cutoff_date
            search_criteria = f'(FROM "{EMAIL_SENDER}" BEFORE {cutoff_date_str})'
            messages = self.mail.search(['FROM', EMAIL_SENDER, 'BEFORE', cutoff_date_str])
            
            if not messages:
                logger.info("📭 Nu există emailuri vechi de șters")
                return
            
            logger.info(f"📬 Găsite {len(messages)} emailuri vechi")
            
            deleted_count = 0
            for email_id in messages:
                try:
                    # Copiază în Trash înainte de ștergere
                    self.mail.copy([email_id], "[Gmail]/Trash")
                    # Marchează pentru ștergere
                    self.mail.set_flags([email_id], [b'\\Deleted'])
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"⚠️  Eroare la ștergerea emailului {email_id}: {e}")
            
            # Execută ștergerea efectivă
            self.mail.expunge()
            logger.info(f"✅ {deleted_count} emailuri șterse cu succes!")
            
        except Exception as e:
            logger.error(f"❌ Eroare la curățarea emailurilor: {e}", exc_info=True)
    
    def process_new_email(self, email_id: int) -> bool:
        """
        Procesează un email nou.
        
        Args:
            email_id: ID-ul emailului de procesat
            
        Returns:
            True dacă procesarea a reușit, False altfel
        """
        try:
            # Fetch emailul
            msg_data = self.mail.fetch([email_id], ['RFC822'])
            
            if not msg_data or email_id not in msg_data:
                logger.warning(f"Nu s-a putut fetch emailul {email_id}")
                return False
            
            raw_email = msg_data[email_id][b'RFC822']
            msg = email.message_from_bytes(raw_email)
            
            # Verifică expeditorul
            from_addr = msg.get('From', '')
            if EMAIL_SENDER not in from_addr:
                logger.debug(f"Email ignorat (expeditor: {from_addr})")
                return True
            
            # Extrage conținutul HTML
            html_content = self._extract_html_from_message(msg)
            if not html_content:
                logger.warning(f"Niciun conținut HTML găsit în email {email_id}")
                return False
            
            logger.info(f"📧 Procesare email #{email_id}...")
            
            # Parsează HTML și extrage datele comenzii
            order_data = parse_order_html(html_content)
            
            if not order_data:
                logger.error(f"❌ Parsare eșuată pentru email {email_id}")
                return False
            
            # Extract order ID from wrapped structure
            order_id = order_data["comanda"]["id_intern_comanda"]
            
            # Verifică duplicate
            if is_order_processed(order_id):
                self.mail.set_flags([email_id], [b'\\Seen'])
                return True
            
            # Salvează JSON-ul
            if save_order_json(order_data):
                logger.info(f"✅ Comandă #{order_id} procesată cu succes!")
                
                # Incrementează contorul și verifică dacă trebuie să ruleze cleanup
                count = self.increment_order_counter()
                logger.info(f"📊 Comenzi procesate: {count}/{CLEANUP_THRESHOLD}")
                
                if count >= CLEANUP_THRESHOLD:
                    self.cleanup_old_emails()
                    self.reset_order_counter()
                
                # Marchează emailul ca citit
                self.mail.set_flags([email_id], [b'\\Seen'])
                return True
            else:
                logger.error(f"❌ Eroare la salvarea comenzii #{order_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Eroare la procesarea emailului {email_id}: {e}", exc_info=True)
            return False
    
    def _extract_html_from_message(self, msg) -> Optional[str]:
        """Extrage conținutul HTML dintr-un mesaj email."""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        return part.get_payload(decode=True).decode('utf-8', 'ignore')
            elif msg.get_content_type() == "text/html":
                return msg.get_payload(decode=True).decode('utf-8', 'ignore')
        except Exception as e:
            logger.error(f"Eroare la extragerea HTML: {e}")
        return None
    
    def process_existing_unread(self):
        """Procesează emailurile necitite existente la pornire."""
        try:
            logger.info("📬 Verificare emailuri necitite existente...")
            
            messages = self.mail.search(['UNSEEN', 'FROM', EMAIL_SENDER])
            
            if not messages:
                logger.info("📭 Niciun email necitit existent")
                return
            
            logger.info(f"📨 Găsite {len(messages)} emailuri necitite")
            
            for email_id in messages:
                self.process_new_email(email_id)
                
        except Exception as e:
            logger.error(f"❌ Eroare la procesarea emailurilor existente: {e}", exc_info=True)
    
    def idle_loop(self):
        """
        Loop principal IDLE care ascultă pentru emailuri noi.
        Rulează continuu până când self.running devine False.
        """
        logger.info("=" * 80)
        logger.info("🚀 START Email Listener cu IMAP IDLE")
        logger.info("=" * 80)
        
        while self.running:
            try:
                # Conectare dacă nu suntem conectați
                if not self.mail:
                    if not self.connect():
                        logger.warning("⏳ Reîncerc conexiunea în 30 secunde...")
                        time.sleep(30)
                        continue
                    
                    # Procesează emailurile necitite existente
                    self.process_existing_unread()
                
                # Start IDLE mode
                logger.info("👂 Ascult pentru emailuri noi (IDLE mode)...")
                
                self.mail.idle()
                logger.info("✅ IDLE mode activat")
                
                # Așteaptă notificări
                start_time = time.time()
                
                while self.running and (time.time() - start_time) < self.idle_timeout:
                    try:
                        responses = self.mail.idle_check(timeout=30)
                        
                        if responses:
                            logger.info(f"📥 IDLE notificare primită: {responses}")
                            
                            # Verifică dacă sunt emailuri noi
                            has_new_emails = False
                            for response in responses:
                                if len(response) >= 2:
                                    if b'EXISTS' in response or b'RECENT' in response or b'FETCH' in response:
                                        logger.info(f"🔔 Email nou detectat! {response}")
                                        has_new_emails = True
                            
                            # Procesează emailurile noi
                            if has_new_emails:
                                self.mail.idle_done()
                                logger.info("⏸️  Ieșit din IDLE mode pentru procesare")
                                
                                messages = self.mail.search(['UNSEEN', 'FROM', EMAIL_SENDER])
                                
                                if messages:
                                    logger.info(f"📨 Procesare {len(messages)} email(uri) nou(i)")
                                    for email_id in messages:
                                        self.process_new_email(email_id)
                                
                                # Reintrare în IDLE
                                self.mail.idle()
                                logger.info("▶️  Reintrare în IDLE mode")
                                start_time = time.time()
                        
                    except self.mail.Error as e:
                        logger.error(f"IMAP Error în IDLE: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Eroare în IDLE check: {e}")
                        break
                
                # Timeout IDLE - reconectare
                if time.time() - start_time >= self.idle_timeout:
                    logger.info("⏰ IDLE timeout - reconectare...")
                    try:
                        self.mail.idle_done()
                    except:
                        pass
                    self.disconnect()
                    
            except Exception as e:
                logger.error(f"❌ Eroare în loop principal: {e}", exc_info=True)
                
                # --- MODIFICARE ---
                # Trimite notificare de eroare CRITICĂ
                try:
                    NotificationService().send_error_notification(
                        error_message=str(e),
                        context="EmailListener - idle_loop (CRITICĂ)"
                    )
                except:
                    pass  # Nu vrem să crăpăm dacă nici notificarea nu merge
                # --- SFÂRȘIT MODIFICARE ---
                
                logger.info("⏳ Reîncerc în 30 secunde...")
                self.disconnect()
                time.sleep(30)
        
        # Cleanup
        try:
            if self.mail:
                self.mail.idle_done()
        except:
            pass
        
        logger.info("=" * 80)
        logger.info("🛑 STOP Email Listener")
        logger.info("=" * 80)
    
    def start(self):
        """Pornește listener-ul."""
        try:
            self.idle_loop()
        except KeyboardInterrupt:
            logger.info("\n⚠️  KeyboardInterrupt primit - oprire...")
        finally:
            self.running = False
            self.disconnect()
    
    def stop(self):
        """Oprește listener-ul."""
        logger.info("🛑 Oprire listener...")
        self.running = False
