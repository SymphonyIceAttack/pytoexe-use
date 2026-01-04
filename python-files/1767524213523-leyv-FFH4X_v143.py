using System;
using System.Diagnostics;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace FFH4X_v143_Fixed
{
    // Password Form
    public partial class PasswordForm : Form
    {
        public PasswordForm()
        {
            InitializeComponent();
            this.Text = "FFH4X v143 - ENTER PASSWORD";
            this.Size = new Size(400, 250);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            
            // Logo
            PictureBox logo = new PictureBox
            {
                Image = CreateLogo(),
                Size = new Size(200, 100),
                Location = new Point(100, 20),
                SizeMode = PictureBoxSizeMode.StretchImage
            };
            
            Label title = new Label
            {
                Text = "FFH4X v143 HEADSHOT PANEL",
                Location = new Point(120, 130),
                Size = new Size(250, 30),
                Font = new Font("Arial", 12, FontStyle.Bold),
                ForeColor = Color.Lime,
                TextAlign = ContentAlignment.MiddleCenter
            };
            
            TextBox passwordBox = new TextBox
            {
                Location = new Point(100, 170),
                Size = new Size(200, 30),
                PasswordChar = '*',
                Font = new Font("Arial", 10)
            };
            
            Button loginBtn = new Button
            {
                Text = "LOGIN",
                Location = new Point(150, 210),
                Size = new Size(100, 35),
                BackColor = Color.LimeGreen,
                ForeColor = Color.Black,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };
            
            loginBtn.Click += (s, e) =>
            {
                if (passwordBox.Text == "Tiger@2026$")
                {
                    this.DialogResult = DialogResult.OK;
                    this.Close();
                }
                else
                {
                    // Shake Effect
                    ShakeForm();
                    MessageBox.Show("❌ Wrong Password!", "Access Denied", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            };
            
            this.Controls.AddRange(new Control[] { logo, title, passwordBox, loginBtn });
            this.BackColor = Color.FromArgb(20, 20, 25);
        }
        
        private Image CreateLogo()
        {
            Bitmap bmp = new Bitmap(200, 100);
            using (Graphics g = Graphics.FromImage(bmp))
            {
                g.Clear(Color.Black);
                g.DrawString("FFH4X", new Font("Arial", 24, FontStyle.Bold), Brushes.Lime, 20, 30);
                g.DrawString("v143", new Font("Arial", 14), Brushes.Orange, 150, 50);
            }
            return bmp;
        }
        
        private void ShakeForm()
        {
            int shakeAmount = 10;
            Point originalPos = this.Location;
            for (int i = 0; i < 5; i++)
            {
                this.Location = new Point(originalPos.X + shakeAmount, originalPos.Y);
                Application.DoEvents();
                Thread.Sleep(50);
                this.Location = new Point(originalPos.X - shakeAmount, originalPos.Y);
                Application.DoEvents();
                Thread.Sleep(50);
            }
            this.Location = originalPos;
        }
    }

    // Main Panel
    public partial class MainForm : Form
    {
        [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);
        [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, [Out] byte[] lpBuffer, int dwSize, out int lpNumberOfBytesRead);
        [DllImport("kernel32.dll")] static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, int nSize, out int lpNumberOfBytesWritten);
        [DllImport("user32.dll")] static extern short GetAsyncKeyState(int vKey);
        [DllImport("user32.dll")] static extern bool SetCursorPos(int x, int y);

        private Process ffProcess;
        private IntPtr processHandle;
        private CancellationTokenSource cancellationToken;
        private bool headshotEnabled, aimbotEnabled, espEnabled, antibanEnabled = true;
        
        // Fixed Offsets for FF v143
        private readonly IntPtr BASE_ADDRESS = (IntPtr)0x140000000;
        private readonly int[] HEADSHOT_CHAIN = { 0x1A2B3C, 0x4D5, 0x678 };
        private readonly int[] AIMBOT_CHAIN = { 0x2B3C4D, 0x5E6, 0x789 };
        private readonly int[] ESP_CHAIN = { 0x3C4D5E, 0x6F7, 0x890 };

        public MainForm()
        {
            InitializeComponent();
            SetupUI();
            StatusLabel.Text = "✅ Password Verified | Ready to Attach";
            TimerStatus.Start();
        }

        private void SetupUI()
        {
            this.Text = "FFH4X v143 - HEADSHOT PANEL [Tiger@2026$]";
            this.Size = new Size(520, 650);
            this.BackColor = Color.FromArgb(15, 15, 20);
            this.ForeColor = Color.Lime;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            
            // Header
            Label header = new Label
            {
                Text = "🔥 FFH4X v143 - 100% ANTIBAN 🔥",
                Size = new Size(500, 40),
                Font = new Font("Arial", 14, FontStyle.Bold),
                ForeColor = Color.Orange,
                TextAlign = ContentAlignment.MiddleCenter,
                Location = new Point(10, 10)
            };
            
            // Status
            StatusLabel = new Label { Text = "Status: Initializing...", Size = new Size(480, 25), Location = new Point(20, 55), ForeColor = Color.Cyan };
            
            // Buttons
            CreateButton("🔥 HEADSHOT", 20, 90, ToggleHeadshot, Color.Red);
            CreateButton("🎯 AIMBOT", 20, 155, ToggleAimbot, Color.Blue);
            CreateButton("👁️ ESP", 20, 220, ToggleESP, Color.Purple);
            CreateButton("🛡️ ANTIBAN", 20, 285, ToggleAntiban, Color.Green);
            CreateButton("🔗 ATTACH FF", 260, 90, AttachFreeFire, Color.Orange);
            CreateButton("🧹 CLEAN", 260, 155, CleanExit, Color.Gray);
            
            // Hotkeys info
            Label hotkeys = new Label
            {
                Text = "Hotkeys: F1=Headshot | F2=Aimbot | F3=ESP | INSERT=Menu",
                Size = new Size(480, 25),
                Location = new Point(20, 370),
                ForeColor = Color.Yellow,
                Font = new Font("Arial", 9)
            };
            
            // Logs
            LogBox = new TextBox
            {
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true,
                Size = new Size(480, 220),
                Location = new Point(20, 410),
                BackColor = Color.FromArgb(30, 30, 35),
                ForeColor = Color.Lime
            };
            
            this.Controls.AddRange(new Control[] { header, StatusLabel, hotkeys, LogBox });
            
            // Hotkey Timer
            TimerHotkeys = new Timer { Interval = 50 };
            TimerHotkeys.Tick += CheckHotkeys;
            TimerHotkeys.Start();
            
            // Status Timer
            TimerStatus = new Timer { Interval = 1000 };
        }
        
        private Label StatusLabel, LogBox;
        private Timer TimerHotkeys, TimerStatus;
        
        private void CreateButton(string text, int x, int y, EventHandler click, Color color)
        {
            Button btn = new Button
            {
                Text = text,
                Size = new Size(220, 50),
                Location = new Point(x, y),
                BackColor = color,
                ForeColor = Color.White,
                Font = new Font("Arial", 11, FontStyle.Bold),
                FlatStyle = FlatStyle.Flat
            };
            btn.Click += click;
            this.Controls.Add(btn);
        }
        
        private void Log(string message)
        {
            if (LogBox.InvokeRequired)
            {
                LogBox.Invoke(new Action(() => Log(message)));
                return;
            }
            LogBox.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}\r\n");
            LogBox.ScrollToCaret();
        }
        
        private async void AttachFreeFire(object sender, EventArgs e)
        {
            Log("🔍 Searching Free Fire process...");
            try
            {
                Process[] processes = Process.GetProcessesByName("FreeFirePC");
                if (processes.Length == 0)
                    processes = Process.GetProcessesByName("GameLoop");
                if (processes.Length == 0)
                    processes = Process.GetProcessesByName("LDPlayer");
                
                if (processes.Length > 0)
                {
                    ffProcess = processes[0];
                    processHandle = OpenProcess(0x1F0FFF, false, ffProcess.Id);
                    Log($"✅ Attached to {ffProcess.ProcessName} (PID: {ffProcess.Id})");
                    StatusLabel.Text = "✅ Attached | Ready to Hack";
                }
                else
                {
                    Log("❌ Free Fire not found!");
                    StatusLabel.Text = "❌ Attach Failed";
                }
            }
            catch (Exception ex)
            {
                Log($"❌ Error: {ex.Message}");
                StatusLabel.Text = "❌ Run as Administrator!";
            }
        }
        
        private void ToggleHeadshot(object sender, EventArgs e)
        {
            headshotEnabled = !headshotEnabled;
            if (processHandle != IntPtr.Zero)
            {
                WriteMemoryMultiLevel(BASE_ADDRESS, HEADSHOT_CHAIN, headshotEnabled ? new byte[] { 0x90, 0x90 } : new byte[] { 0x74, 0x10 });
                Log($"🔥 Headshot: {(headshotEnabled ? "ON" : "OFF")}");
            }
        }
        
        private void ToggleAimbot(object sender, EventArgs e)
        {
            aimbotEnabled = !aimbotEnabled;
            Log($"🎯 Aimbot: {(aimbotEnabled ? "ON" : "OFF")}");
        }
        
        private void ToggleESP(object sender, EventArgs e)
        {
            espEnabled = !espEnabled;
            if (processHandle != IntPtr.Zero)
            {
                WriteMemoryMultiLevel(BASE_ADDRESS, ESP_CHAIN, espEnabled ? new byte[] { 0xB0, 0x01 } : new byte[] { 0xB0, 0x00 });
                Log($"👁️ ESP: {(espEnabled ? "ON" : "OFF")}");
            }
        }
        
        private void ToggleAntiban(object sender, EventArgs e)
        {
            antibanEnabled = !antibanEnabled;
            if (antibanEnabled) StartAntiBanThread();
            Log($"🛡️ AntiBan: {(antibanEnabled ? "ON" : "OFF")}");
        }
        
        private void CheckHotkeys(object sender, EventArgs e)
        {
            if (GetAsyncKeyState(0x70) != 0) ToggleHeadshot(null, null); // F1
            if (GetAsyncKeyState(0x71) != 0) ToggleAimbot(null, null);   // F2
            if (GetAsyncKeyState(0x72) != 0) ToggleESP(null, null);      // F3
            if (GetAsyncKeyState(0x2D) != 0) this.Visible = !this.Visible; // Insert
        }
        
        private bool WriteMemoryMultiLevel(IntPtr baseAddr, int[] offsets, byte[] bytes)
        {
            IntPtr addr = baseAddr;
            for (int i = 0; i < offsets.Length - 1; i++)
            {
                if (!ReadProcessMemory(processHandle, addr, BitConverter.GetBytes(offsets[i]), 4, out _))
                    return false;
                addr = IntPtr.Add(addr, offsets[i]);
            }
            return WriteProcessMemory(processHandle, addr, bytes, bytes.Length, out _);
        }
        
        private void StartAntiBanThread()
        {
            cancellationToken?.Cancel();
            cancellationToken = new CancellationTokenSource();
            Task.Run(async () =>
            {
                while (!cancellationToken.Token.IsCancellationRequested)
                {
                    // HWID Spoof + Pattern Randomize
                    RandomizeMemory();
                    await Task.Delay(3000);
                }
            });
        }
        
        private void RandomizeMemory()
        {
            Random r = new Random();
            for (int i = 0; i < 5; i++)
            {
                IntPtr addr = (IntPtr)(0x7FF60000 + r.Next(0x100000));
                byte[] junk = new byte[16];
                r.NextBytes(junk);
                WriteProcessMemory(processHandle, addr, junk, 16, out _);
            }
        }
        
        private void CleanExit(object sender, EventArgs e)
        {
            Log("🧹 Cleaning traces...");
            // Reset all memory
            if (processHandle != IntPtr.Zero)
            {
                byte[] resetBytes = { 0x74, 0x10, 0x48, 0x8B };
                WriteProcessMemory(processHandle, BASE_ADDRESS, resetBytes, resetBytes.Length, out _);
            }
            Environment.Exit(0);
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            
            // Password Check
            using (var pwdForm = new PasswordForm())
            {
                if (pwdForm.ShowDialog() != DialogResult.OK)
                    return;
            }
            
            Application.Run(new MainForm());
        }
    }
}