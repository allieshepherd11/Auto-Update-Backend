from pywinauto import Application,Desktop
import sys
import time
import pandas as pd
from collections import defaultdict


class Qrod():
    def __init__(self):
        self.app_title = "Echometer QRod 3.1"

        if not self.is_open():
            Application().start('C:/Program Files (x86)/Echometer/QRod 3/QRod.exe')
            time.sleep(.5)

        self.app = Application().connect(title=self.app_title)
        time.sleep(1)

        window = self.app.window(title=self.app_title)
        self.sl_dropdown = window.SurfaceStrokeLengthComboBox
        self.diam_dropdown = window.PumpDiameterDComboBox
        self.pump_depth_dropdown = window.PumpDepthComboBox
        self.rod_taper = window.APIRodNumberComboBox

        self.anchor_tbg_btn = window.AnchoredTubingButton
        self.sb_btn = window.TotalSinkerBarWeightButton
        self.main_calc_btn = window.CalculateButton

        self.pump_depth_input = window.PumpDepthEdit
        self.sp_gr_input = window.FluidSpecificGravityEdit
        self.spm_input = window.Edit5

        if not self.anchor_tbg_btn.is_checked():
            self.anchor_tbg_btn.click()


        self.rod_taper.select('86')
        self.sp_gr_input.set_text('0.99') 

        self.window = window
        self.run_sb_window()

    def is_open(self):
        windows = Desktop(backend="win32").windows()
        for w in windows:
            if self.app_title in w.window_text():
                return True
        return False

    def run_sb_window(self):
        self.sb_btn.click()
        time.sleep(1)

        sb_window = Application().connect(title="Sinker Bar Calculator").window(title="Sinker Bar Calculator")
        time.sleep(.5)
        sb_calc_btn = sb_window.CalculateButton
        sb_use_btn = sb_window.UseCalculationButton

        sb_calc_btn.click()
        sb_use_btn.click()
        time.sleep(1)

    def print_control_ids(self):
        self.main_calc_btn.click()
        with open("control_identifiers.txt", "w", encoding="utf-8") as f:
            sys.stdout = f  # Redirect output to file
            self.window.print_control_identifiers()
            sys.stdout = sys.__stdout__  # Reset stdout back to normal

    def set_input_params(self,depth,sl,diam,spm):
        self.pump_depth_dropdown.select(depth)
        self.sl_dropdown.select(sl)
        self.diam_dropdown.select(diam)
        self.spm_input.set_text(spm) 

    def get_results(self):
        self.main_calc_btn.click()
        time.sleep(.5)
        min_unit = self.window.Static7.window_text()
        rod_taper = self.window.Static8.window_text()
        peak_gb_torque = self.window.Static52.window_text()
        bpd_eff = self.window.Static36.window_text()
        top_rod_loading = self.window.Static37.window_text()

        #for i in range(30,50):
        #    key = f'Static{i}'
        #    print(i,self.window[key].window_text())

        return {"min_unit":min_unit,"rod_taper":rod_taper,"peak_gb_torque":peak_gb_torque,"bpd_eff":bpd_eff,"top_rod_loading":top_rod_loading}


if __name__ == '__main__':
    qrod = Qrod()
    input_sets = [['5,000','120.00','1.500','10'],['7,000','144.00','1.750','7']]
    #for i in input_sets:
    #    qrod.set_input_params(*i)
    #    res = qrod.get_results()#re
    #    print(res)
    #exit()
    df_inputs = pd.read_excel("C:/Users/plaisancem/Downloads/qrod_inputs.xlsx")

    depths = [f"{int(i):,}" for i in df_inputs['pump depth'] if i == i]
    sls = [f"{int(i):.2f}" for i in df_inputs['stroke length'] if i == i]
    dias = [f"{float(i):.3f}" for i in df_inputs['pump diameter'] if i == i]
    spms = [str(i) for i in df_inputs['spm'] if i == i]

    df_res = defaultdict(list)
    l = len(depths)*len(sls)*len(dias)*len(spms)
    cnt=1
    for depth in depths:
        for d in dias:
            for sl in sls:
                for spm in spms:
                    print(l-cnt)
                    cnt+=1
                    qrod.set_input_params(depth,sl,d,spm)
                    res = qrod.get_results()#return min_unit,rod_taper,peak_gb_torque,bpd_eff,top_rod_loading
                    df_res['depth'].append(depth)
                    df_res['pump diameter'].append(d)
                    df_res['stroke length'].append(sl)
                    df_res['spm'].append(spm)

                    for k,v in res.items():
                        df_res[k].append(v)

    pd.DataFrame(df_res).to_excel('qrod_results.xlsx',index=False)