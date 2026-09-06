package np.sathi.ai
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
class SathiNotificationListener:NotificationListenerService(){override fun onNotificationPosted(sbn:StatusBarNotification?){sbn?:return;getSharedPreferences("sathi",MODE_PRIVATE).edit().putString("last_notification_package",sbn.packageName).apply()}}
