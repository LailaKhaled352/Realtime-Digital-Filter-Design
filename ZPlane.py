import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import signal
import csv

class ZPlane(QWidget):
    def __init__(self, zplane_widget, filter_respone, real_time_filter):
        super().__init__(zplane_widget)
        # Zeros and Poles
        self.zeros = np.array([], dtype=complex)
        self.poles = np.array([], dtype=complex)
        self.all_pass_zeros = np.array([], dtype=complex)
        self.all_pass_poles = np.array([], dtype=complex)
        self.zplane_widget=zplane_widget
        self.filter_response= filter_respone
        self.real_time_filter =real_time_filter
        self.pole_mode= False 
        self.dragging = None #for dragging event
        self.delete_mode=  False
        self.conjugate_mode= False

        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []
        
        # Matplotlib Figure and Canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(zplane_widget)
        layout.addWidget(self.canvas)
        zplane_widget.setLayout(layout)
        # Create subplot
        self.ax = self.figure.add_subplot(111)
        self.ax.grid(True)
        # Set tight layout for better fit
        self.figure.tight_layout()

        self.plot_z_plane()

        #mouse connection
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_release)
    
    #Undo/Redo Functionality
    def save_state(self): #before change, save the current state first
        self.undo_stack.append((self.zeros.copy(), self.poles.copy()))
        self.redo_stack.clear()  # Clear redo stack when a new change is made

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append((self.zeros.copy(), self.poles.copy()))  # Save current state to redo
            self.zeros, self.poles = self.undo_stack.pop()  # Restore previous state
            self.plot_z_plane()
            self.plot_filter_response()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append((self.zeros.copy(), self.poles.copy()))  # Save current state to undo
            self.zeros, self.poles = self.redo_stack.pop()  # Restore redone state
            self.plot_z_plane()
            self.plot_filter_response()

    def plot_z_plane(self, zeros=None, poles=None,state=False):

        self.ax.clear()  # Clear any previous plot

        zeros_from_allpass = np.asarray(zeros).flatten() if zeros is not None else np.array([], dtype=complex)
        poles_from_allpass = np.asarray(poles).flatten() if poles is not None else np.array([], dtype=complex) 
       # poles_from_allpass = poles 
        print (f"zeros in  originalzplane:{zeros_from_allpass} ")
       
        if state:
          mask_zeros = np.isin(self.zeros, zeros_from_allpass)
          mask_poles = np.isin(self.poles, poles_from_allpass) 
          self.zeros = np.delete(self.zeros, np.where(mask_zeros)[0])
          self.poles = np.delete(self.poles, np.where(mask_poles)[0])

        else:
            self.zeros = np.unique(np.concatenate((self.zeros, zeros_from_allpass))) if zeros_from_allpass.size > 0 else self.zeros
            self.poles = np.unique(np.concatenate((self.poles, poles_from_allpass))) if poles_from_allpass.size > 0 else self.poles

        # Plot the unit circle
        print(f"originallist:{self.zeros}")
        
        theta = np.linspace(0, 2 * np.pi, 100)
        self.ax.plot(np.cos(theta), np.sin(theta), linestyle='--', color='gray', label='Unit Circle')
        # Add labels and grid
        self.ax.axhline(0, color='black', linewidth=0.5)
        self.ax.axvline(0, color='black', linewidth=0.5)
        self.ax.grid(color='gray', linestyle='--', linewidth=0.5)
        self.ax.legend()
        self.ax.set_title('Zeros and Poles in the Z-Plane')
        self.ax.set_xlabel('Real Part')
        self.ax.set_ylabel('Imaginary Part')
        self.ax.set_xlim(-2, 2)
        #self.ax.set_ylim(-15, 15)

        if self.zeros.size > 0:
            print(f"zeros that draw :{self.zeros}")
            self.ax.scatter(self.zeros.real, self.zeros.imag, s=50, color='red', label='Zeros', marker='o')
        if self.poles.size > 0:
            self.ax.scatter(self.poles.real, self.poles.imag, s=50, color='blue', label='Poles', marker='x')

        if  zeros_from_allpass is not None and zeros_from_allpass.size > 0 and not state : # Use .size to check non-empty array
         self.ax.scatter(zeros_from_allpass.real, zeros_from_allpass.imag, s=50, color='red', label='Zeros', marker='o')
        if poles_from_allpass is not None and poles_from_allpass.size > 0 and not state :  # Use .size to check non-empty array
         self.ax.scatter(poles_from_allpass.real, poles_from_allpass.imag, s=50, color='blue', label='Poles', marker='x')
        #self.plot_z_plane()
        self.plot_filter_response()

        #colors changes
        self.ax.set_facecolor('black')  # Set the plot background to black
        self.figure.patch.set_facecolor('black')  # Set the figure background to black
        self.ax.grid(color='white', linestyle='--', linewidth=0.5)  # Change grid color
        self.ax.spines['bottom'].set_color('white')  
        self.ax.spines['top'].set_color('white')  
        self.ax.spines['left'].set_color('white')  
        self.ax.spines['right'].set_color('white')  
        self.ax.xaxis.label.set_color('white')  
        self.ax.yaxis.label.set_color('white')  
        self.ax.title.set_color('white')  
        self.ax.tick_params(colors='white')  # Change tick color
        self.ax.axhline(0, color='white', linewidth=0.5)
        self.ax.axvline(0, color='white', linewidth=0.5)
        self.ax.plot(np.cos(theta), np.sin(theta), linestyle='--', color='white', label='Unit Circle')

        # Refresh the canvas
        self.canvas.draw()






    def append_all_pass_zeros_poles(self, zeros_all_pass, poles_all_pass):
    # Append the zeros and poles of the all-pass filter
     self.all_pass_zeros = np.append(self.all_pass_zeros, zeros_all_pass)
     self.all_pass_poles = np.append(self.all_pass_poles, poles_all_pass)
        
     self.zeros = np.append(self.zeros, zeros_all_pass)
     self.poles = np.append(self.poles, poles_all_pass)
    
   
     # Replot Z-plane and frequency response
     self.plot_z_plane()
     self.plot_filter_response()  

    def remove_all_pass_zeros_poles(self, zeros_all_pass, poles_all_pass):
    # Remove the zeros and poles from the lists
     mask_zeros = np.isin(self.zeros, zeros_all_pass)
     mask_poles = np.isin(self.poles, poles_all_pass) 
     self.zeros = np.delete(self.zeros, np.where(mask_zeros)[0])
     self.poles = np.delete(self.poles, np.where(mask_poles)[0])

# Replot Z-plane and frequency response
     self.plot_z_plane()
     self.plot_filter_response()

    def toggle_mode_to_zeros(self):
        self.pole_mode= False
    def toggle_mode_to_poles(self):
        self.pole_mode= True
   
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        click_pos = complex(event.xdata, event.ydata)
        tolerance = 0.05  # Distance threshold for selecting a point
        self.dragging = None

        # Check if the click is near an existing zero or pole
        if self.pole_mode and len(self.poles)!=0:
            distances = np.abs(self.poles - click_pos)
            if distances.min() < tolerance:
                self.dragging = ('pole', distances.argmin()) #returns the index of the minimum value
        elif len(self.zeros)!=0:
            distances = np.abs(self.zeros - click_pos)
            if distances.min() < tolerance:
                self.dragging = ('zero', distances.argmin())
        
        if self.delete_mode:
            self.save_state()
            point_type, index = self.dragging
            if point_type =='pole':
               self.poles= np.delete(self.poles, index)
            elif point_type =='zero':
                self.zeros= np.delete(self.zeros, index)
            self.plot_z_plane()
            self.plot_filter_response()

        # If neither dragging an existing point nor deleting, add a new one at this position
        elif self.dragging is None:
            self.save_state()
            if self.pole_mode:
                new_pole = click_pos #get data coordinates relative to the plot
                self.poles = np.append(self.poles, new_pole)
                self.ax.scatter(new_pole.real,new_pole.imag, s=50, color='blue', label='Poles', marker='x')
                if self.conjugate_mode and click_pos.imag != 0:
                    self.poles = np.append(self.poles, new_pole.conjugate())
                    self.ax.scatter(new_pole.real,-1*new_pole.imag, s=50, color='blue', label='Poles', marker='x')
            
            elif not self.pole_mode: 
                new_zero= click_pos
                self.zeros = np.append(self.zeros, new_zero)
                self.ax.scatter(new_zero.real, new_zero.imag, s=50, color='red', label='Zeros', marker='o')
                if self.conjugate_mode and click_pos.imag != 0:
                    self.zeros = np.append(self.zeros, new_zero.conjugate())
                    self.ax.scatter(new_zero.real, -1*new_zero.imag, s=50, color='red', label='Zeros', marker='o')
            self.plot_filter_response()
            self.canvas.draw()
    
    def on_mouse_move(self, event):
        if self.dragging and event.inaxes == self.ax:
        # Update the position of the dragged point
            new_pos = complex(event.xdata, event.ydata)
            point_type, index = self.dragging
            if point_type == 'pole':
                self.poles[index] = new_pos
            elif point_type == 'zero':
                self.zeros[index] = new_pos

    def on_release(self, event):
        if self.dragging:
            self.save_state()
            self.plot_z_plane()
            self.plot_filter_response()
            self.dragging = None

    def clear_all(self):
        self.save_state()
        self.poles= np.array([], dtype=complex)
        self.zeros= np.array([], dtype=complex)
        self.plot_z_plane()
        self.plot_filter_response()
    
    def clear_poles(self):
        self.save_state()
        self.poles= np.array([], dtype=complex)
        self.plot_z_plane()
        self.plot_filter_response()

    def clear_zeros(self):
        self.save_state()
        self.zeros= np.array([], dtype=complex)
        self.plot_z_plane()
        self.plot_filter_response()

    def toggle_delete(self):
        self.delete_mode= not self.delete_mode
    
    def toggle_conjugate(self):
        self.conjugate_mode= not self.conjugate_mode
    
    def swap_zeros_poles(self):
        self.save_state()
        self.poles, self.zeros= self.zeros, self.poles
        self.plot_z_plane()
        self.plot_filter_response()
    
    def enforce_conjugate_pairs(self,arr):
        arr_conj = np.conj(arr[np.iscomplex(arr)])
        return np.hstack([arr, arr_conj])
    
    def compute_filter_coefficients(self):
        z = self.enforce_conjugate_pairs(self.zeros)
        p = self.enforce_conjugate_pairs(self.poles)
        b,a = signal.zpk2tf(z, p, 1)
        return b,a
    
    def compute_zeros_poles_from_coefficients(self, b,a):
       self.zeros, self.poles,_ =signal.tf2zpk(b,a)
       self.plot_z_plane()
    
    def get_poles(self):
        return self.poles
    
    def get_zeros(self):
        return self.zeros


    def save_filter(self): #save poles and zeros into csv file
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)", options=options)

        if not file_path:
            return  # User canceled the save operation

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Type", "Real", "Imaginary"])
            # Save zeros
            for z in self.zeros:
                writer.writerow(["zero", z.real, z.imag])
            # Save poles
            for p in self.poles:
                writer.writerow(["pole", p.real, p.imag])

    def load_from_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Load File", "", "CSV Files (*.csv);;Text Files (*.txt)", options=options)

        if not file_path:
            return  # User canceled the load operation
        
        zeros, poles = [], []
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row[0] == "zero":
                    zeros.append(complex(float(row[1]), float(row[2])))
                elif row[0] == "pole":
                    poles.append(complex(float(row[1]), float(row[2])))

        # Save state before loading new data
        self.save_state()
        #convert lists to numpy arrays 
        self.zeros = np.array(zeros, dtype=complex)
        self.poles = np.array(poles, dtype=complex)
        self.plot_z_plane()
        self.plot_filter_response()

    def plot_filter_response(self):
        b,a = self.compute_filter_coefficients()
        self.filter_response.plot_filter_response(b,a)
        self.real_time_filter.set_coef(b,a)
