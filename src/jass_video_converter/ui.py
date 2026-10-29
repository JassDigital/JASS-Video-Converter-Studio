import sys, subprocess
from pathlib import Path
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import *
from .engine import MEDIA, build_command, find_executable, is_media_file

class Worker(QThread):
    log=Signal(str); progress=Signal(int); finished_message=Signal(str)
    def __init__(self,ffmpeg,files,out,fmt,quality,start,end):
        super().__init__(); self.ffmpeg=ffmpeg; self.files=files; self.out=out; self.fmt=fmt; self.quality=quality; self.start_at=start; self.end_at=end; self.cancelled=False; self.proc=None
    def cancel(self):
        self.cancelled=True
        if self.proc and self.proc.poll() is None: self.proc.terminate()
    def run(self):
        total=len(self.files)
        for i,src in enumerate(self.files):
            if self.cancelled: break
            dest=Path(self.out)/(Path(src).stem+"_converted."+self.fmt)
            n=1
            while dest.exists(): dest=Path(self.out)/(Path(src).stem+f"_converted_{n}."+self.fmt); n+=1
            try:
                cmd=build_command(self.ffmpeg,src,str(dest),self.fmt,self.quality,self.start_at,self.end_at)
                self.log.emit(f"[{i+1}/{total}] {src}")
                self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
                for line in self.proc.stdout:
                    if self.cancelled: self.proc.terminate(); break
                    if line.strip(): self.log.emit(line.strip())
                rc=self.proc.wait()
                if rc==0 and dest.exists(): self.log.emit("SUCCESS: "+str(dest))
                else:
                    self.log.emit(f"FAILED (exit {rc}): {src}")
                    if dest.exists():
                        try: dest.unlink()
                        except OSError: pass
            except Exception as e: self.log.emit(f"ERROR: {e}")
            self.progress.emit(int((i+1)*100/total))
        self.finished_message.emit("Cancelled." if self.cancelled else "Queue finished.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("JASS Video Converter Studio v0.1.0"); self.resize(1000,680); self.worker=None
        w=QWidget(); v=QVBoxLayout(w); title=QLabel("JASS Video Converter Studio"); title.setStyleSheet("font-size:22px;font-weight:bold"); v.addWidget(title)
        v.addWidget(QLabel("Batch convert media, extract audio, and optionally trim clips. Original files are preserved."))
        f=QHBoxLayout(); self.ffmpeg=QLineEdit(find_executable("ffmpeg") or ""); browse=QPushButton("Browse ffmpeg.exe"); browse.clicked.connect(self.browse_ffmpeg); f.addWidget(QLabel("FFmpeg")); f.addWidget(self.ffmpeg,1); f.addWidget(browse); v.addLayout(f)
        buttons=QHBoxLayout()
        for text,fn in [("Add files",self.add_files),("Add folder",self.add_folder),("Remove selected",self.remove),("Clear queue",self.clear)]:
            x=QPushButton(text); x.clicked.connect(fn); buttons.addWidget(x)
        v.addLayout(buttons)
        self.table=QTableWidget(0,3); self.table.setHorizontalHeaderLabels(["Input file","Type","Size"]); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSelectionMode(QAbstractItemView.ExtendedSelection); self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); v.addWidget(self.table,1)
        row=QHBoxLayout(); self.fmt=QComboBox(); self.fmt.addItems(["mp4","mkv","avi","mov","webm","mp3","wav","flac"]); self.quality=QComboBox(); self.quality.addItems(["Smaller file","Balanced","High quality"]); self.out=QLineEdit(str(Path.home()/"Videos"/"JASS-Conversions")); ob=QPushButton("Choose output"); ob.clicked.connect(self.choose_out)
        row.addWidget(QLabel("Format")); row.addWidget(self.fmt); row.addWidget(QLabel("MP4 quality")); row.addWidget(self.quality); row.addWidget(QLabel("Output")); row.addWidget(self.out,2); row.addWidget(ob); v.addLayout(row)
        tr=QHBoxLayout(); self.start=QLineEdit(); self.start.setPlaceholderText("Start e.g. 00:00:05 (optional)"); self.end=QLineEdit(); self.end.setPlaceholderText("End e.g. 00:00:20 (optional)"); tr.addWidget(QLabel("Trim")); tr.addWidget(self.start); tr.addWidget(self.end); v.addLayout(tr)
        ctl=QHBoxLayout(); self.go=QPushButton("Convert queue"); self.cancel_btn=QPushButton("Cancel"); self.cancel_btn.setEnabled(False); self.bar=QProgressBar(); ctl.addWidget(self.go); ctl.addWidget(self.cancel_btn); ctl.addWidget(self.bar,1); v.addLayout(ctl)
        self.log=QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumBlockCount(2500); v.addWidget(self.log,1); self.setCentralWidget(w)
        self.go.clicked.connect(self.convert); self.cancel_btn.clicked.connect(self.cancel)
    def browse_ffmpeg(self):
        p,_=QFileDialog.getOpenFileName(self,"Select ffmpeg.exe",str(Path.home()),"Executable (*.exe);;All files (*)")
        if p:self.ffmpeg.setText(p)
    def choose_out(self):
        p=QFileDialog.getExistingDirectory(self,"Output folder",self.out.text())
        if p:self.out.setText(p)
    def add_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,"Select media",str(Path.home()),"Media ("+" ".join("*"+x for x in sorted(MEDIA))+");;All files (*)"); self.add(paths)
    def add_folder(self):
        p=QFileDialog.getExistingDirectory(self,"Select folder",str(Path.home()))
        if p:self.add([str(x) for x in Path(p).rglob("*") if x.is_file() and is_media_file(x)])
    def add(self,paths):
        have={self.table.item(r,0).text() for r in range(self.table.rowCount())}
        for p in paths:
            x=Path(p)
            if not x.is_file() or not is_media_file(x) or str(x) in have:continue
            r=self.table.rowCount(); self.table.insertRow(r); self.table.setItem(r,0,QTableWidgetItem(str(x))); self.table.setItem(r,1,QTableWidgetItem(x.suffix.upper())); self.table.setItem(r,2,QTableWidgetItem(f"{x.stat().st_size/1048576:.1f} MB"))
    def remove(self):
        for r in sorted({i.row() for i in self.table.selectedIndexes()},reverse=True):self.table.removeRow(r)
    def clear(self):self.table.setRowCount(0)
    def convert(self):
        ff=self.ffmpeg.text().strip()
        if not ff or not Path(ff).is_file():QMessageBox.warning(self,"FFmpeg missing","Install FFmpeg or browse to ffmpeg.exe.");return
        sources=[self.table.item(r,0).text() for r in range(self.table.rowCount())]
        if not sources:QMessageBox.information(self,"Queue empty","Add media files first.");return
        try:Path(self.out.text()).mkdir(parents=True,exist_ok=True)
        except OSError as e:QMessageBox.critical(self,"Output error",str(e));return
        self.log.clear(); self.bar.setValue(0); self.go.setEnabled(False); self.cancel_btn.setEnabled(True)
        self.worker=Worker(ff,sources,self.out.text(),self.fmt.currentText(),self.quality.currentText(),self.start.text(),self.end.text())
        self.worker.log.connect(self.log.appendPlainText); self.worker.progress.connect(self.bar.setValue); self.worker.finished_message.connect(self.finished); self.worker.start()
    def cancel(self):
        if self.worker:self.worker.cancel()
    def finished(self,msg):
        self.log.appendPlainText(msg); self.go.setEnabled(True); self.cancel_btn.setEnabled(False); QMessageBox.information(self,"Conversion",msg)

def main():
    app=QApplication(sys.argv); app.setStyle("Fusion"); w=MainWindow(); w.show(); return app.exec()
