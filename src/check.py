"""
This module provides tools for transforming and executing PlusCal code. It includes 
functionalities for processing PlusCal code, translating it to TLA+, and running model 
checking.
"""

import os
import subprocess
import time
import shutil

def exec_cmd_simple(command, timeout=600):
    """
    Executes a command in the shell, with a timeout.
    This method will not return the output of the command.
    """
    res = subprocess.Popen(command, shell=True,
                           stdout=subprocess.STDOUT, stderr=subprocess.STDOUT)
    t_beginning = time.time()
    seconds_passed = 0
    while True:
        if res.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            res.terminate()
            res.returncode = 1
            return False, "timeout"
        time.sleep(0.1)
    if res.returncode != 0:
        return False, "returncode != 0"

    return True, ""

def exec_cmd(cmd, timeout=6000):
    """
    Executes a command in the shell, with a timeout.
    This method will return the output of the command.
    """
    ret = ""
    res = subprocess.Popen(cmd, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t_beginning = time.time()
    seconds_passed = 0
    while True:
        if res.poll() is not None:
            break
        ret = ret + res.stdout.read().decode("utf-8")
        seconds_passed = time.time() - t_beginning
        if seconds_passed > timeout:
            res.terminate()
            res.returncode = 1
            return res
        time.sleep(0.1)
    ret = ret + res.stdout.read().decode("utf-8")
    return ret

class Model:
    """
    A class to manage the lifecycle of a PlusCal model, including code generation,
    translation, and model checking.
    """
    def __init__(self, module_name, profiles):
        self.module_name = module_name
        self.path = f"examples/output/{module_name}/"
        self.file_path = f"{self.path}{module_name}.tla"
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.mc_path = f"{self.path}MC.tla"
        self.profiles = profiles.convert(module=module_name)
        # self.trans_cmd = f"java -cp ./tool/tla2tools.jar pcal.trans -nocfg {self.file_path}"
        self.trans_cmd = f"java -jar ./tool/trans.jar -nocfg {self.file_path}"
        # self.check_cmd = f"java -jar ./tool/tla2tools.jar {self.mc_path}"
        self.check_cmd = f"java -jar ./tool/tlc.jar {self.mc_path} -tsim -deadlock"
        

    def save(self):
        """
        Saves the generated PlusCal code to the specified file path.
        This method writes the PlusCal code to the file specified by 'file_path'.
        """
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.profiles)

    def insert_time(self):
        """
        Inserts time-related annotations at the beginning of the PlusCal code.
        """
        return "__time = 0\n" + "__interval = 0\n"

    def insert_label(self, miss_labels):
        """
        Inserts labels into the PlusCal code at specified line and column positions.
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for l, c in miss_labels:
            lines[l-1] = lines[l-1][:c-1] + f"Label_{l}_{c}: " + lines[l-1][c-1:]

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def trans(self):
        """
        Translates the PlusCal code to TLA+.
        """
        print(f"translating: {self.trans_cmd}")
        res = exec_cmd(self.trans_cmd)
        miss_labels = []
        output = res.split("\n")
        for line in output:
            if line.startswith("     line "):
                l = line.split("line")[1].split(", ")[0]
                c = line.split("line")[1].split(", ")[1].split("column")[1]
                l = int(l)
                if c.endswith("."):
                    c = int(c[:-1])
                c = int(c)
                miss_labels.append((l, c))
        if len(miss_labels) > 0:
            miss_labels.sort()
            miss_labels.reverse()
            print(miss_labels)
            self.insert_label(miss_labels)
            res = exec_cmd(self.trans_cmd)
            output = res
        print(output)
        print("translating done")
        # Generate MC.tla
        # MC = f"---- MODULE MC ----\nEXTENDS {self.module_name}, TLC\n" + \
        #     "const_1 == FALSE\n" + "================================\n"
        mc = f"---- MODULE MC ----\nEXTENDS {self.module_name}, TLC\n" + \
             "================================\n"
        with open(self.mc_path, "w", encoding="utf-8") as f:
            f.write(mc)
    
        # MC_CFG = f"CONSTANT\n    defaultInitValue <- const_1\nINIT\nInit\nNEXT\nNext\n"
        # # Generate MC.cfg
        # with open(f"{self.path}/MC.cfg", "w") as f:
        #     f.write(MC_CFG)

    def run(self):
        """
        Executes the model checking process.
        """
        print(f"running: {self.check_cmd}")
        exec_cmd(self.check_cmd)
        # move the output file to the output folder
        files = os.listdir("./")
        report = "./report"

        history = "./report/history"
        if not os.path.exists(history):
            os.makedirs(history)
        history_files = os.listdir(report)
        for f in history_files:
            if f.startswith("perStateStats_"):
                shutil.move(f"{report}/{f}", history)
        for f in files:
            if f.startswith("perStateStats_"):
                shutil.move(f, report)

    def check(self):
        """
        Runs the entire process of saving, translating, and model checking the PlusCal code.
        """
        # model checking
        self.save()
        self.trans()
        exec_cmd(self.check_cmd) 

# if __name__ == '__main__':
#     path = "./examples/real/wire.tla"
#     with open(path, "r", encoding="utf-8") as f:
#         src = f.read()
#     model = Model("wire", src)
#     model.check()