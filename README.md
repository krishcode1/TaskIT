# TaskIT

Aplicación Android para organizar tareas académicas, construida con Python, Flet y SQLite.

## Requisitos

- Python 3.10 o superior.
- [uv](https://docs.astral.sh/uv/) para gestionar dependencias.
- Android Studio con:
  - Android SDK Platform 36 (compileSdk del proyecto).
  - Android SDK Platform 35 (mínimo que verifica Flet).
  - Android SDK Build-Tools 36 y 34.0.0.
  - Android SDK Platform-Tools.
  - NDK 28.2.13676358.
  - Un emulador o un dispositivo físico con depuración USB.
- Java 17. Si Flet no encuentra un JDK válido, descarga Temurin 17 automáticamente.

Flet descarga e instala automáticamente la versión de Flutter que necesita; no es necesario instalarlo por separado.

## Preparar el entorno

```powershell
uv sync
```

Configurar la ubicación del SDK e instalar los paquetes requeridos:

```powershell
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME

$android = "$env:ANDROID_HOME\cmdline-tools\latest\bin\android.exe"
& $android sdk install platforms/android-35
& $android sdk install platforms/android-36
& $android sdk install build-tools/34.0.0
& $android sdk install ndk/28.2.13676358
```

También se pueden instalar desde el SDK Manager de Android Studio. Las licencias deben estar aceptadas.

Si `flutter doctor` está disponible en el PATH, se puede usar para comprobar el toolchain:

```powershell
flutter doctor -v
```

Debe aparecer el Android toolchain sin errores.

## Ejecutar y probar

```powershell
# Aplicación de escritorio
uv run flet run

# Pruebas
uv run pytest
```

## Generar el APK

```powershell
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME

# Si Flet instaló su propio JDK 17:
$env:JAVA_HOME = "$env:USERPROFILE\java\17.0.13+11"

# Limpiar compilaciones anteriores (opcional pero recomendado)
Remove-Item -Recurse -Force build

# Compilar
uv run flet build apk -v
```

La primera compilación descarga dependencias de Gradle y el runtime de Python para Android, y puede tardar varios minutos.

El APK se genera en:

```text
build\apk\taskit.apk
```

Es un APK de tipo release firmado con la clave de depuración. Sirve para probar e instalar por sideload, pero no para publicar en Play Store. Para publicación se necesitaría un AAB con firma propia.

### Instalar en un dispositivo o emulador

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r build\apk\taskit.apk
```

Para iniciar un emulador:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -list-avds
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd <nombre_del_avd>
```

El emulador x86_64 necesita aceleración por hardware. Si aparece el error `x86_64 emulation currently requires hardware acceleration`, instala el Android Emulator hypervisor driver desde el SDK Manager de Android Studio o usa un dispositivo físico.

## Configuración de la app

| Propiedad | Valor |
| --- | --- |
| Nombre | TaskIT |
| `org` | `com.taskit` |
| `bundle_id` | `com.taskit.app` |
| Versión | `0.1.0` (`versionCode` 1) |
| `compileSdk` | 36 |
| `minSdk` | 24 |
| `targetSdk` | 36 |
| Icono | `src/assets/icon.png` (1024×1024) |

El APK de release se firma con la clave de depuración de Android. Es válido para pruebas e instalación por sideload, no para publicar en Play Store.

## Almacenamiento de datos

Las tareas se guardan en SQLite dentro del directorio privado de la aplicación. En Android, Flet define `FLET_APP_STORAGE_DATA` como:

```text
/data/user/0/com.taskit.app/files/data
```

El archivo es `taskit.db`. Los datos persisten al cerrar y volver a abrir la app y al actualizarla con el mismo `bundle_id`. Se eliminan al desinstalar la aplicación. No se requieren permisos de almacenamiento.

## Estructura

```text
src/
  assets/       Iconos y recursos
  ui/           Componentes de la interfaz
  db.py         Acceso a SQLite
  models.py     Modelo de tarea
  main.py       Punto de entrada
tests/          Pruebas de base de datos e interfaz
pyproject.toml  Dependencias y configuración de Flet
```
