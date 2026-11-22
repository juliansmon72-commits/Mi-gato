# Se ejecuta en la nube después de "npx cap add android": agrega permisos e íconos.
import os
from PIL import Image, ImageDraw

man = 'android/app/src/main/AndroidManifest.xml'
s = open(man, encoding='utf-8').read()
perms = ['ACCESS_COARSE_LOCATION', 'ACCESS_FINE_LOCATION', 'FOREGROUND_SERVICE',
         'FOREGROUND_SERVICE_LOCATION', 'POST_NOTIFICATIONS', 'WAKE_LOCK', 'ACTIVITY_RECOGNITION']
add = ''.join('    <uses-permission android:name="android.permission.%s" />\n' % p
              for p in perms if p not in s)
s = s.replace('<application', add + '    <application', 1)
open(man, 'w', encoding='utf-8').write(s)

icon = Image.open('icon-512.png').convert('RGBA')
fg = Image.open('icon-maskable-512.png').convert('RGBA')
for d, (l, f) in {'mdpi': (48, 108), 'hdpi': (72, 162), 'xhdpi': (96, 216),
                  'xxhdpi': (144, 324), 'xxxhdpi': (192, 432)}.items():
    r = 'android/app/src/main/res/mipmap-' + d
    if not os.path.isdir(r):
        continue
    sq = icon.resize((l, l), Image.LANCZOS)
    sq.save(r + '/ic_launcher.png')
    mask = Image.new('L', (l, l), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, l - 1, l - 1], fill=255)
    rd = sq.copy(); rd.putalpha(mask); rd.save(r + '/ic_launcher_round.png')
    fg.resize((f, f), Image.LANCZOS).save(r + '/ic_launcher_foreground.png')

bg = 'android/app/src/main/res/values/ic_launcher_background.xml'
open(bg, 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#F27D84</color>\n</resources>\n')
print('listo')


# ---- Plugin propio: contador de pasos del sistema (sigue contando con la app cerrada) ----
pkgdir = 'android/app/src/main/java/com/migato/app'
os.makedirs(pkgdir, exist_ok=True)
open(pkgdir + '/StepCounterPlugin.java', 'w', encoding='utf-8').write("""package com.migato.app;

import android.Manifest;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

@CapacitorPlugin(
    name = "StepCounter",
    permissions = { @Permission(alias = "activity", strings = { Manifest.permission.ACTIVITY_RECOGNITION }) }
)
public class StepCounterPlugin extends Plugin {

    private SensorManager sm;
    private SensorEventListener listener;
    private volatile float latest = -1f;

    private boolean ensureListener() {
        if (listener != null) return true;
        sm = (SensorManager) getContext().getSystemService(Context.SENSOR_SERVICE);
        Sensor sensor = sm.getDefaultSensor(Sensor.TYPE_STEP_COUNTER);
        if (sensor == null) return false;
        listener = new SensorEventListener() {
            @Override
            public void onSensorChanged(SensorEvent event) {
                latest = event.values[0];
            }

            @Override
            public void onAccuracyChanged(Sensor sensor, int accuracy) {}
        };
        sm.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_NORMAL);
        return true;
    }

    @PluginMethod
    public void read(PluginCall call) {
        if (Build.VERSION.SDK_INT >= 29 && getPermissionState("activity") != PermissionState.GRANTED) {
            requestPermissionForAlias("activity", call, "permCallback");
            return;
        }
        doRead(call);
    }

    @PermissionCallback
    private void permCallback(PluginCall call) {
        if (getPermissionState("activity") == PermissionState.GRANTED) {
            doRead(call);
        } else {
            call.reject("PERMISSION_DENIED");
        }
    }

    private void doRead(final PluginCall call) {
        if (!ensureListener()) {
            call.reject("NO_SENSOR");
            return;
        }
        if (latest >= 0) {
            JSObject result = new JSObject();
            result.put("steps", (double) latest);
            call.resolve(result);
            return;
        }
        final Handler handler = new Handler(Looper.getMainLooper());
        final int[] tries = { 0 };
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (latest >= 0) {
                    JSObject result = new JSObject();
                    result.put("steps", (double) latest);
                    call.resolve(result);
                } else if (++tries[0] >= 20) {
                    call.reject("TIMEOUT");
                } else {
                    handler.postDelayed(this, 200);
                }
            }
        }, 200);
    }

    @Override
    protected void handleOnDestroy() {
        if (sm != null && listener != null) sm.unregisterListener(listener);
        super.handleOnDestroy();
    }
}
""")
open(pkgdir + '/MainActivity.java', 'w', encoding='utf-8').write("""package com.migato.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(StepCounterPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
""")


# ---- ícono chico (blanco) para las notificaciones ----
from PIL import Image as _I, ImageDraw as _D
ic = _I.new('RGBA', (96, 96), (0, 0, 0, 0)); dr = _D.Draw(ic) if hasattr(_D, 'Draw') else _D.Draw(ic)
dr.ellipse([14, 38, 34, 62], fill='white'); dr.ellipse([30, 18, 50, 42], fill='white')
dr.ellipse([46, 18, 66, 42], fill='white'); dr.ellipse([62, 38, 82, 62], fill='white')
dr.ellipse([26, 50, 70, 86], fill='white')
os.makedirs('android/app/src/main/res/drawable', exist_ok=True)
ic.save('android/app/src/main/res/drawable/ic_stat_icon_config_sample.png')
