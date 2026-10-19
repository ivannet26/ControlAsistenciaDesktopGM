; installer_setup.iss
#define MyAppName "Control de Asistencia"
#define MyAppVersion "1.0.7"
#define MyAppPublisher "GM Ingenieros y Consultores"
#define MyAppExeName "ControlAsistencia.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=ControlAsistencia_Setup_v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

; Usamos el icono del ejecutable (asegúrate de que existe en app/assets/)
SetupIconFile=app\assets\favicon.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; --- TEXTOS PERSONALIZADOS (Le dan el toque corporativo) ---
[Messages]
WelcomeLabel1=Bienvenido a {#MyAppName}
WelcomeLabel2=Este asistente instalará la aplicación de {#MyAppPublisher} en su equipo. Se recomienda cerrar otras aplicaciones antes de continuar.
FinishedHeadingLabel=¡Instalación completada!
FinishedLabel=El programa {#MyAppName} de {#MyAppPublisher} se ha instalado correctamente.
ClickFinish=Haga clic en Finalizar para cerrar el asistente.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Tus archivos de la app
Source: "dist\ControlAsistencia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; El instalador de Microsoft
Source: "VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 1. Instalar Visual C++ (silencioso).
Filename: "{tmp}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Instalando dependencias de Microsoft..."; Flags: waituntilterminated; Check: not IsVCRedistInstalled
; 2. Lanzar tu aplicación al finalizar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// --- FUNCIÓN PARA DETECTAR EL VISUAL C++ ---
function IsVCRedistInstalled(): Boolean;
var
  Installed: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) and (Installed = 1);
end;

// --- MENSAJE FINAL PERSONALIZADO ---
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    MsgBox('¡Control de Asistencia se ha instalado correctamente!' + #13#10 + #13#10 +
           'Recuerde abrir el programa con permisos de Administrador para que el rastreador de URLs funcione sin problemas.', 
           mbInformation, MB_OK);
end;