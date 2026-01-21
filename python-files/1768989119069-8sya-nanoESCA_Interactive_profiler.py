import numpy as np
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from scipy.special import erf
from scipy.optimize import curve_fit, OptimizeWarning
from skimage.measure import profile_line
import tifffile
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import pandas as pd
import os
import warnings

# Error Function Model
def erf_model(x, offset, amp, center, d):
    return offset + (amp/2) * (1 + erf((x - center) / (max(d, 0.1) * np.sqrt(2))))

class NanoEscaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NanoESCA Interactive Profiler")
        
        # Internal State
        self.image = None
        self.p1 = self.p2 = self.active_node = None
        self.lw = 5
        self.move_mode = False
        self.press_start = None
        self.orig_p1 = self.orig_p2 = None
        self.last_results = {}
        self.tiff_path = ""

        # UI Layout
        self.setup_sidebar()
        self.setup_plots()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        plt.close('all')
        self.root.quit()
        self.root.destroy()

    def setup_plots(self):
        plot_container = tk.Frame(self.root)
        plot_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 1. Image Figure
        self.fig_img = Figure(figsize=(6, 5), dpi=100)
        self.ax_img = self.fig_img.add_subplot(111)
        
        self.canvas_img = FigureCanvasTkAgg(self.fig_img, master=plot_container)
        
        # NEW: Add Matplotlib Navigation Toolbar (Zoom/Pan/Home)
        toolbar = NavigationToolbar2Tk(self.canvas_img, plot_container)
        toolbar.update()
        self.canvas_img.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.line_artist, = self.ax_img.plot([], [], 'r-o', lw=2, markersize=2, zorder=10)

        # 2. Fit Figure
        self.fig_fit = Figure(figsize=(6, 3), dpi=100)
        self.fit_ax = self.fig_fit.add_subplot(111)
        self.canvas_fit = FigureCanvasTkAgg(self.fig_fit, master=plot_container)
        self.canvas_fit.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.data_plot, = self.fit_ax.plot([], [], 'k.', label='Data')
        self.fit_plot, = self.fit_ax.plot([], [], 'r-', lw=2, label='Fit')
        
        # Interaction Events
        self.canvas_img.mpl_connect('button_press_event', self.on_press)
        self.canvas_img.mpl_connect('button_release_event', self.on_release)
        self.canvas_img.mpl_connect('motion_notify_event', self.on_move)
        self.root.bind('<s>', lambda e: self.save_data())

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif *.tiff")])
        if path:
            self.tiff_path = path
            self.image = tifffile.imread(path)
            self.ax_img.clear()
            self.ax_img.imshow(self.image, cmap='gray')
            self.line_artist, = self.ax_img.plot([], [], 'r-o', lw=2, markersize=2, zorder=10)
            self.canvas_img.draw()

    def on_press(self, event):
        if event.inaxes != self.ax_img or self.image is None: return
        if event.button == 3:
            self.p1 = self.p2 = None
            self.line_artist.set_data([], [])
            self.canvas_img.draw_idle()
            return

        curr = (event.ydata, event.xdata)
        if event.key == 'shift' and self.p1 and self.p2:
            self.move_mode, self.press_start = True, curr
            self.orig_p1, self.orig_p2 = self.p1, self.p2
        elif self.p1 and np.hypot(event.xdata - self.p1[1], event.ydata - self.p1[0]) < 20:
            self.active_node = 'p1'
        elif self.p2 and np.hypot(event.xdata - self.p2[1], event.ydata - self.p2[0]) < 20:
            self.active_node = 'p2'
        else:
            self.p1, self.p2, self.active_node = curr, None, 'p2'

    def on_move(self, event):
        if event.inaxes != self.ax_img: return
        if self.move_mode:
            dy, dx = event.ydata - self.press_start[0], event.xdata - self.press_start[1]
            self.p1 = (self.orig_p1[0] + dy, self.orig_p1[1] + dx)
            self.p2 = (self.orig_p2[0] + dy, self.orig_p2[1] + dx)
        elif self.active_node:
            curr_y, curr_x = event.ydata, event.xdata
            ref = self.p2 if self.active_node == 'p1' else self.p1
            dy, dx = abs(curr_y - ref[0]), abs(curr_x - ref[1])
            new_p = (curr_y, ref[1]) if dy > dx else (ref[0], curr_x)
            if self.active_node == 'p1': self.p1 = new_p
            else: self.p2 = new_p
        else: return

        self.line_artist.set_data([self.p1[1], self.p2[1]], [self.p1[0], self.p2[0]])
        self.canvas_img.draw_idle()
        self.update_fit()

    def on_release(self, event):
        self.active_node = self.move_mode = False

    def setup_sidebar(self):
        sidebar = tk.Frame(self.root, width=200, bg='gray80', padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(sidebar, text="Load TIFF", command=self.load_file).pack(fill=tk.X, pady=5)
        
        # Space Entry with Enter Binding
        tk.Label(sidebar, text="Space (r/k/px):", bg='gray80').pack(anchor='w')
        self.ent_space = tk.Entry(sidebar)
        self.ent_space.insert(0, "k")
        self.ent_space.pack(fill=tk.X)
        self.ent_space.bind('<Return>', lambda e: self.update_fit())

        # C-Factor Entry with Enter Binding
        tk.Label(sidebar, text="C-Factor (unit/px):", bg='gray80').pack(anchor='w')
        self.ent_cf = tk.Entry(sidebar)
        self.ent_cf.insert(0, "1.312")
        self.ent_cf.pack(fill=tk.X)
        self.ent_cf.bind('<Return>', lambda e: self.update_fit())

        # Line Width Entry with Enter Binding
        tk.Label(sidebar, text="Line Width (px):", bg='gray80').pack(anchor='w', pady=(10, 0))
        self.ent_lw = tk.Entry(sidebar)
        self.ent_lw.insert(0, "5")
        self.ent_lw.pack(fill=tk.X)
        self.ent_lw.bind('<Return>', lambda e: self.on_width_change())

        tk.Button(sidebar, text="Save Data (S)", command=self.save_data, bg='lightgreen').pack(fill=tk.X, pady=20)
        
        tk.Label(sidebar, text="Controls:\nL-Click: Start/Drag\nShift+L-Click: Move\nEnter (in box): Update\nR-Click: Clear\n'S' Key: Save", 
                 bg='gray80', justify=tk.LEFT).pack(side=tk.BOTTOM)

    def on_width_change(self):
        """Specifically handles width-driven visual updates + re-fit."""
        try:
            val = int(self.ent_lw.get())
            # Sync the visual thickness of the red line
            self.line_artist.set_linewidth(max(1, val/2)) 
            self.canvas_img.draw_idle()
            self.update_fit()
        except ValueError:
            pass

    def update_fit(self):
        """Primary fitting logic triggered by movement or box value changes."""
        if not (self.p1 and self.p2): return
        
        try:
            # 1. Get current metadata from UI
            current_lw = int(self.ent_lw.get())
            cf = float(self.ent_cf.get())
            space_val = self.ent_space.get().lower()
            unit = {'r':'µm', 'k':'mÅ\u207b\u00b9'}.get(space_val, 'px')
            if unit == 'px': cf = 1.0 # Force CF to 1 if px is selected
            
            if current_lw < 1: current_lw = 1
        except ValueError:
            return # Ignore malformed inputs until Enter is pressed correctly

        # 2. Extract and Fit
        profile = profile_line(self.image, self.p1, self.p2, linewidth=current_lw, mode='constant')
        if len(profile) < 10: return
        
        x = np.arange(len(profile))
        p0 = [np.min(profile), np.max(profile)-np.min(profile), len(profile)/2, 2.0]
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OptimizeWarning)
            try:
                popt, pcov = curve_fit(erf_model, x, profile, p0=p0)
                perr = np.sqrt(np.diag(pcov)) if not np.isinf(pcov).all() else np.zeros(4)
                
                # popt[3] is the sigma (standard deviation)
                w1684 = 2 * abs(popt[3]) * cf
                w1684_err = 2 * abs(perr[3]) * cf
                percent = (w1684_err / w1684) * 100 if w1684 != 0 else 0

                # 3. Update Plots & UI
                self.data_plot.set_data(x, profile)
                self.fit_plot.set_data(x, erf_model(x, *popt))
                self.fit_ax.relim()
                self.fit_ax.autoscale_view()
                self.fit_ax.set_title(f"16-84%: {w1684:.3f} ± {w1684_err:.3f} {unit} ({percent:.1f}%)")
                self.canvas_fit.draw_idle()
                
                # 4. Store current state for saving
                self.last_results = {
                    'x': x, 'y': profile, 'fit': erf_model(x, *popt), 
                    'w1684': w1684, 'w_err': w1684_err, 'cf': cf, 'unit': unit
                }
            except:
                pass




    def save_data(self):
        if not self.last_results: return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fdir = os.path.dirname(self.tiff_path)
        
        df = pd.DataFrame({'px': self.last_results['x'], 'raw': self.last_results['y'], 'fit': self.last_results['fit']})
        header = f"16-84 Width: {self.last_results['w1684']:.4f} +/- {self.last_results['w_err']:.4f} {self.last_results['unit']}\n"
        
        # CSV with encoding for unicode units
        csv_path = os.path.join(fdir, f"fit_{ts}.csv")
        with open(csv_path, 'w', encoding='utf-8-sig') as f:
            f.write(header)
            df.to_csv(f, index=False)
        
        # Save both Figures
        self.fig_img.savefig(os.path.join(fdir, f"overlay_{ts}.png"), bbox_inches='tight')
        self.fig_fit.savefig(os.path.join(fdir, f"fit_plot_{ts}.png"), bbox_inches='tight')
        messagebox.showinfo("Saved", f"Results saved to:\n{fdir}")

if __name__ == "__main__":
    plt.ioff()
    root = tk.Tk()
    app = NanoEscaApp(root)
    root.mainloop()
