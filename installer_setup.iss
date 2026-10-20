; installer_setup.iss
#define MyAppName "Control de Asistencia"
#define MyAppVersion "1.0.8"
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
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Icono de la app
SetupIconFile=app\assets\favicon.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; --- TEXTOS PERSONALIZADOS ---
[Messages]
spanish.WelcomeLabel1=Bienvenido a {#MyAppName}
spanish.WelcomeLabel2=Este asistente instalará la versión {#MyAppVersion} de {#MyAppName} de {#MyAppPublisher} en su equipo.%n%nSe recomienda cerrar otras aplicaciones antes de continuar.
spanish.FinishedHeadingLabel=¡Instalación completada!
spanish.FinishedLabel={#MyAppName} se ha instalado correctamente.%n%nRecuerde abrir el programa con permisos de Administrador para que el rastreador de URLs funcione sin problemas.
spanish.ClickFinish=Haga clic en Finalizar para cerrar el asistente.

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
const
  // Colores en formato BGR para Inno Setup (Azul oscuro y gris)
  COLOR_FONDO  = $1F180D;  // #0d181f (Fondo de la app)
  COLOR_PANEL  = $2C2316;  // #16232c (Fondo de paneles)
  COLOR_TEXTO  = $F3EDE6;  // #e6edf3 (Texto claro)
  COLOR_SUAVE  = $AFA08E;  // #8ea0af (Texto secundario)
  COLOR_ACENTO = $FFB82E;  // #2eb8ff (Azul celeste)

// --- FUNCIÓN PARA DETECTAR EL VISUAL C++ ---
function IsVCRedistInstalled(): Boolean;
var
  Installed: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) and (Installed = 1);
end;

// --- PINTAR CONTROLES ---
procedure PintarControles();
var
  i: Integer;
  C: TComponent;
begin
  for i := 0 to WizardForm.ComponentCount - 1 do
  begin
    C := WizardForm.Components[i];

    if C is TNewStaticText then
      TNewStaticText(C).Font.Color := COLOR_TEXTO
    else if C is TNewCheckBox then
      TNewCheckBox(C).Font.Color := COLOR_TEXTO
    else if C is TNewRadioButton then
      TNewRadioButton(C).Font.Color := COLOR_TEXTO
    else if C is TNewCheckListBox then
    begin
      TNewCheckListBox(C).Color := COLOR_PANEL;
      TNewCheckListBox(C).Font.Color := COLOR_TEXTO;
      TNewCheckListBox(C).BorderStyle := bsNone;
    end
    else if C is TRichEditViewer then
    begin
      TRichEditViewer(C).Color := COLOR_PANEL;
      TRichEditViewer(C).Font.Color := COLOR_TEXTO;
    end
    else if C is TEdit then
    begin
      TEdit(C).Color := COLOR_PANEL;
      TEdit(C).Font.Color := COLOR_TEXTO;
    end;
  end;
end;

// --- FRANJA LATERAL ---
procedure CrearFranjaLateral(Pagina: TNewNotebookPage);
var
  P: TPanel;
begin
  P := TPanel.Create(WizardForm);
  P.Parent := Pagina;
  P.Caption := '';
  P.BevelOuter := bvNone;
  P.ParentBackground := False;
  P.Color := COLOR_ACENTO;
  P.SetBounds(0, 0, ScaleX(8), Pagina.Height);
  P.Anchors := [akLeft, akTop, akBottom];
end;

// --- LÍNEA DE ENCABEZADO ---
procedure CrearLineaEncabezado();
var
  P: TPanel;
begin
  P := TPanel.Create(WizardForm);
  P.Parent := WizardForm.MainPanel;
  P.Caption := '';
  P.BevelOuter := bvNone;
  P.ParentBackground := False;
  P.Color := COLOR_ACENTO;
  P.Height := ScaleY(2);
  P.Align := alBottom;
end;

// --- INICIALIZACIÓN DEL WIZARD ---
procedure InitializeWizard();
var
  i: Integer;
  Pie: TNewStaticText;
begin
  // 1) Fondos oscuros
  WizardForm.Color := COLOR_FONDO;
  for i := 0 to WizardForm.OuterNotebook.PageCount - 1 do
    WizardForm.OuterNotebook.Pages[i].Color := COLOR_FONDO;
  for i := 0 to WizardForm.InnerNotebook.PageCount - 1 do
    WizardForm.InnerNotebook.Pages[i].Color := COLOR_FONDO;

  // 2) Ocultar imágenes por defecto
  WizardForm.WizardBitmapImage.Visible := False;
  WizardForm.WizardBitmapImage2.Visible := False;
  WizardForm.WizardSmallBitmapImage.Visible := False;
  WizardForm.Bevel.Visible := False;
  WizardForm.Bevel1.Visible := False;

  // 3) Colores de los controles
  PintarControles();

  // 4) Estilos del encabezado
  WizardForm.MainPanel.Color := COLOR_PANEL;
  WizardForm.PageNameLabel.Font.Color := COLOR_TEXTO;
  WizardForm.PageNameLabel.Font.Style := [fsBold];
  WizardForm.PageDescriptionLabel.Font.Color := COLOR_SUAVE;
  CrearLineaEncabezado();

  // 5) Pantalla de bienvenida
  CrearFranjaLateral(WizardForm.WelcomePage);
  WizardForm.WelcomeLabel1.Left := ScaleX(36);
  WizardForm.WelcomeLabel1.Width := WizardForm.WelcomePage.Width - ScaleX(60);
  WizardForm.WelcomeLabel1.Font.Size := 18;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel1.Font.Color := COLOR_ACENTO;
  WizardForm.WelcomeLabel2.Left := ScaleX(36);
  WizardForm.WelcomeLabel2.Width := WizardForm.WelcomePage.Width - ScaleX(60);
  WizardForm.WelcomeLabel2.Top := WizardForm.WelcomeLabel1.Top + WizardForm.WelcomeLabel1.Height + ScaleY(16);
  WizardForm.WelcomeLabel2.Font.Color := COLOR_TEXTO;

  // 6) Pantalla final
  CrearFranjaLateral(WizardForm.FinishedPage);
  WizardForm.FinishedHeadingLabel.Left := ScaleX(36);
  WizardForm.FinishedHeadingLabel.Width := WizardForm.FinishedPage.Width - ScaleX(60);
  WizardForm.FinishedHeadingLabel.Font.Size := 18;
  WizardForm.FinishedHeadingLabel.Font.Style := [fsBold];
  WizardForm.FinishedHeadingLabel.Font.Color := COLOR_ACENTO;
  WizardForm.FinishedLabel.Left := ScaleX(36);
  WizardForm.FinishedLabel.Width := WizardForm.FinishedPage.Width - ScaleX(60);
  WizardForm.FinishedLabel.Top := WizardForm.FinishedHeadingLabel.Top + WizardForm.FinishedHeadingLabel.Height + ScaleY(16);
  WizardForm.FinishedLabel.Font.Color := COLOR_TEXTO;
  WizardForm.RunList.Left := ScaleX(36);
  WizardForm.RunList.Width := WizardForm.FinishedPage.Width - ScaleX(60);

  // 7) Texto de pie
  Pie := TNewStaticText.Create(WizardForm);
  Pie.Parent := WizardForm;
  Pie.Caption := '{#MyAppName}  ·  v{#MyAppVersion}';
  Pie.Font.Color := COLOR_SUAVE;
  Pie.Left := ScaleX(20);
  Pie.Top := WizardForm.NextButton.Top + ScaleY(6);
end;

// --- MENSAJE FINAL EMERGENTE ---
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    MsgBox('¡Control de Asistencia se ha instalado correctamente!' + #13#10 + #13#10 +
           'Recuerde abrir el programa con permisos de Administrador para que el rastreador de URLs funcione sin problemas.', 
           mbInformation, MB_OK);
end;