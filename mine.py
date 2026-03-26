import sys
import os
import random
from itertools import combinations

# --- PySide6 ライブラリのインポート ---
# GUI構築に必要なウィジェット群
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFrame, QComboBox, QCheckBox, 
    QSlider, QGraphicsOpacityEffect, QGroupBox, QTabWidget, QTextEdit
)
# アニメーション、タイマー、座標管理など
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QUrl
# 描画（ペン、ブラシ、フォント）
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QMouseEvent
from PySide6.QtMultimedia import QSoundEffect

# ==========================================
# 言語データ (日本語 / 英語)
# ==========================================
TEXTS = {
    'jp': {
        'tab_main': 'メイン',
        'tab_feat': '機能調整',
        'tab_about': '説明',
        'lang_btn': 'English',
        'grp_game': 'ゲーム設定',
        'lbl_w': '幅 (W)',
        'lbl_h': '高さ (H)',
        'lbl_b': '爆弾 (%)',
        'grp_vis': '表示設定',
        'lbl_theme': 'テーマ:',
        'chk_detail': '数字・旗を表示',
        'grp_bot': 'ボット知能',
        'lbl_style': '思考:',
        'style_island': '島攻略 (角優先)',
        'style_std': '標準 (走査)',
        'lbl_speed': '速度:',
        'btn_reset': '適用 / リセット',
        'status_ready': '開始するにはクリック',
        'status_ai': '🤖 ロボット思考中...',
        'status_human': '🤷 あなたの番です',
        'status_win': '🏆 任務完了 🏆',
        'status_lose': '💀 ゲームオーバー 💀',
        'feat_anim': 'アニメーション設定',
        'lbl_overlay_dur': 'オーバーレイ時間 (ms):',
        'lbl_overlay_alpha': 'オーバーレイ濃度 (0-255):',
        'feat_sys': 'システム設定',
        'chk_sound': '効果音 (Win/Lose)',
        'about_title': 'LuckSweeper マニュアル',
        'about_text': """
<h2>遊び方</h2>
<p>爆弾を避けながら、すべての安全なマスを開けてください。<br>
最初の1手は必ず安全です。</p>

<h3>テーマについて</h3>
<ul>
<li><b>Modern (デフォルト):</b> フラットで見やすい現代的なデザイン。</li>
<li><b>Sea (海モード):</b> 
    <ul>
    <li><b>青 (海):</b> 危険なし (0)</li>
    <li><b>砂色 (浜):</b> 数字マス (境界)</li>
    <li><b>緑 (陸):</b> 未探索エリア</li>
    </ul>
    ※このモードでは爆弾が島のようにまとまって生成されます。
</li>
<li><b>Classic:</b> 懐かしいWindows 95風のデザイン。</li>
</ul>
"""
    },
    'en': {
        'tab_main': 'Main',
        'tab_feat': 'Features',
        'tab_about': 'About',
        'lang_btn': '日本語',
        'grp_game': 'Game Settings',
        'lbl_w': 'Width',
        'lbl_h': 'Height',
        'lbl_b': 'Mines (%)',
        'grp_vis': 'Visuals',
        'lbl_theme': 'Theme:',
        'chk_detail': 'Show Numbers/Flags',
        'grp_bot': 'Bot Intelligence',
        'lbl_style': 'Style:',
        'style_island': 'Island (Corner)',
        'style_std': 'Standard (Scan)',
        'lbl_speed': 'Speed:',
        'btn_reset': 'APPLY / RESET',
        'status_ready': 'Click to Start',
        'status_ai': '🤖 Bot Thinking...',
        'status_human': '🤷 Human Turn',
        'status_win': '🏆 MISSION PASSED 🏆',
        'status_lose': '💀 WASTED 💀',
        'feat_anim': 'Animation Tweaks',
        'lbl_overlay_dur': 'Overlay Duration (ms):',
        'lbl_overlay_alpha': 'Overlay Alpha (0-255):',
        'feat_sys': 'System Tweaks',
        'chk_sound': 'Sound Effects',
        'about_title': 'LuckSweeper Manual',
        'about_text': """
<h2>How to Play</h2>
<p>Reveal all safe squares without detonating a mine.<br>
The first click is always safe.</p>

<h3>Themes</h3>
<ul>
<li><b>Modern (Default):</b> Clean, flat design.</li>
<li><b>Sea Mode:</b> 
    <ul>
    <li><b>Blue:</b> Safe Sea (0)</li>
    <li><b>Sand:</b> Beach (Numbers)</li>
    <li><b>Green:</b> Unexplored Land</li>
    </ul>
    *Mines are clustered like islands in this mode.
</li>
<li><b>Classic:</b> Retro Windows 95 style.</li>
</ul>
"""
    }
}

# ==========================================
# サウンド管理クラス
# ==========================================
class SoundManager:
    """
    音声ファイルの読み込みと再生を担当。
    ファイルが存在しない場合は標準ビープ音で代用する安全設計。
    """
    def __init__(self):
        self.muted = False
        self.effects = {}
        # 同じフォルダにあるwavファイルを読み込む
        self.load_sound('win', 'win.wav')
        self.load_sound('lose', 'lose.wav')

    def load_sound(self, name, filename):
        if os.path.exists(filename):
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(filename))
            self.effects[name] = effect
        else:
            self.effects[name] = None # ファイルがない場合

    def play(self, name):
        if self.muted: return
        
        # 音声ファイルがあれば再生、なければビープ音
        if name in self.effects and self.effects[name]:
            self.effects[name].play()
        else:
            if name in ['win', 'lose']: 
                QApplication.beep()

# ==========================================
# ゲーム盤面ウィジェット (描画担当)
# ==========================================
class BoardWidget(QWidget):
    """マインスイーパ盤面（画面外カリング付き）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.parent_logic = None

        # グリッド設定
        self.grid_w = 20
        self.grid_h = 20
        self.cells = []
        self.cell_size = 20
        self.offset_x = 0
        self.offset_y = 0

        # ズーム・パン
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._dragging = False
        self._drag_start = None
        
        # 表示設定
        self.theme = 'Modern' 
        self.show_details = True # 数字や旗を表示するかどうか
        
        # アニメーション設定
        self.overlay_anim_duration = 500
        self.overlay_alpha_max = 200
        
        # --- カラーパレット定義 ---
        self.colors = {
            'Sea': {
                'bg': QColor('#2c3e50'),
                'sea': QColor('#2980b9'),
                'sand': QColor('#e6d0a1'),
                'land': QColor('#27ae60'),
                'mine_bg': QColor('#c0392b'),
                'text_base': QColor('#5d4037')
            },
            'Modern': {
                'bg': QColor('#222'),
                'sea': QColor('#fff'),
                'sand': QColor('#fff'),
                'land': QColor('#ddd'),
                'mine_bg': QColor('#e74c3c'),
                'text_base': Qt.black
            },
            'Classic': {
                'bg': QColor('#c0c0c0'),
                'sea': QColor('#c0c0c0'),
                'sand': QColor('#c0c0c0'),
                'land': QColor('#c0c0c0'),
                'mine_bg': QColor('red'),
                'text_base': Qt.black
            },
            'Brazil': {
                'bg': QColor('#004a17'),
                'sea': QColor('#009c3b'),
                'sand': QColor('#ffdf00'),
                'land': QColor('#00a84f'),
                'mine_bg': QColor('#d40000'),
                'text_base': QColor('#002776')
            },
            'Hoover': {
                'bg': QColor('#0a1929'),
                'sea': QColor('#1565c0'),
                'sand': QColor('#ff9800'),
                'land': QColor('#2196f3'),
                'mine_bg': QColor('#ff5722'),
                'text_base': QColor('#0d2137')
            },
            'Retro': {
                'bg': QColor('#0d0d0d'),
                'sea': QColor('#1a0a2e'),
                'sand': QColor('#39ff14'),
                'land': QColor('#2d1b4e'),
                'mine_bg': QColor('#ff073a'),
                'text_base': QColor('#39ff14')
            },
            'Sakura': {
                'bg': QColor('#2d1320'),
                'sea': QColor('#fce4ec'),
                'sand': QColor('#f8bbd0'),
                'land': QColor('#e91e8c'),
                'mine_bg': QColor('#880e4f'),
                'text_base': QColor('#4a0028')
            },
            'Arctic': {
                'bg': QColor('#0a1628'),
                'sea': QColor('#e3f2fd'),
                'sand': QColor('#b3e5fc'),
                'land': QColor('#4682b4'),
                'mine_bg': QColor('#d32f2f'),
                'text_base': QColor('#0d47a1')
            },
            'Sunset': {
                'bg': QColor('#1a0533'),
                'sea': QColor('#ffdab9'),
                'sand': QColor('#ff7043'),
                'land': QColor('#7b1fa2'),
                'mine_bg': QColor('#b71c1c'),
                'text_base': QColor('#3e0066')
            },
            'Hacker': {
                'bg': QColor('#0a0a0a'),
                'sea': QColor('#0a1a0a'),
                'sand': QColor('#0f3b0f'),
                'land': QColor('#1a1a1a'),
                'mine_bg': QColor('#cc0000'),
                'text_base': QColor('#00ff41')
            },
        }
        # 数字ごとの色（1=青, 2=緑...）
        self.num_colors = [Qt.black, QColor('#0000FF'), QColor('#008000'), QColor('#FF0000'),
                           QColor('#000080'), QColor('#800000'), QColor('#008080'), Qt.black]

        # --- GTA風オーバーレイ ("WASTED") ---
        self.overlay_label = QLabel(self)
        self.overlay_label.setAlignment(Qt.AlignCenter) # 画面中央にテキスト配置
        self.overlay_label.setFont(QFont('Impact', 60, QFont.Bold))
        self.overlay_label.hide()
        
        # フェードインアニメーション用エフェクト
        self.opacity_effect = QGraphicsOpacityEffect(self.overlay_label)
        self.overlay_label.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")

    def set_grid_size(self, w, h):
        """グリッドサイズ変更時の更新処理"""
        self.grid_w = w
        self.grid_h = h
        self.update() # 再描画リクエスト

    def show_overlay(self, text, color_hex):
        """GTA風メッセージを表示する"""
        self.overlay_label.setText(text)
        # 背景を半透明の黒、文字色を指定
        self.overlay_label.setStyleSheet(f"color: {color_hex}; background-color: rgba(0,0,0,{self.overlay_alpha_max});")
        
        # 画面全体を覆うようにリサイズ
        self.resize_overlay()
        
        self.overlay_label.show()
        self.overlay_label.raise_() # 最前面へ
        
        # アニメーション開始
        self.anim.setDuration(self.overlay_anim_duration)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def hide_overlay(self):
        self.overlay_label.hide()

    def resizeEvent(self, event):
        """ウィンドウサイズ変更時に呼ばれる"""
        self.resize_overlay()
        super().resizeEvent(event)
        
    def resize_overlay(self):
        """オーバーレイを常に画面全体に合わせる"""
        if self.overlay_label:
            self.overlay_label.resize(self.width(), self.height())
            self.overlay_label.move(0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        theme_cols = self.colors.get(self.theme, self.colors['Modern'])
        painter.fillRect(self.rect(), theme_cols['bg'])

        if not self.cells: return

        avail_w = self.width()
        avail_h = self.height()
        padding = 10

        base_sz_w = (avail_w - padding * 2) / self.grid_w
        base_sz_h = (avail_h - padding * 2) / self.grid_h
        base_cell = max(1, int(min(base_sz_w, base_sz_h)))
        self.cell_size = max(1, int(base_cell * self.zoom))

        total_w = self.cell_size * self.grid_w
        total_h = self.cell_size * self.grid_h
        self.offset_x = (avail_w - total_w) // 2 + self.pan_x
        self.offset_y = (avail_h - total_h) // 2 + self.pan_y

        font_size = max(1, int(self.cell_size * 0.6))
        font_fam = "Courier New" if self.theme == 'Classic' else "Arial"
        painter.setFont(QFont(font_fam, font_size, QFont.Bold))

        for y in range(self.grid_h):
            for x in range(self.grid_w):
                cell = self.cells[y][x]
                rx = self.offset_x + x * self.cell_size
                ry = self.offset_y + y * self.cell_size
                size = self.cell_size

                if rx + size < 0 or ry + size < 0 or rx > avail_w or ry > avail_h:
                    continue

                if self.theme == 'Classic':
                    self.draw_classic(painter, rx, ry, size, cell, theme_cols, font_size)
                else:
                    self.draw_modern_sea(painter, rx, ry, size, cell, theme_cols, font_size)

    def draw_modern_sea(self, p, x, y, s, cell, cols, fs):
        """モダン / 海モードの描画"""
        gap = 0 if s < 5 else 1 # 小さすぎる時は隙間をなくす
        rect = QRect(x, y, s - gap, s - gap)
        
        if cell['revealed']:
            if cell['is_mine']:
                # 爆弾表示
                p.fillRect(rect, cols['mine_bg'])
                if self.show_details and fs > 4:
                    p.setPen(Qt.white)
                    p.drawText(rect, Qt.AlignCenter, "💣")
            else:
                # 海モードなら0は海色、数字は砂色にする
                if self.theme == 'Sea':
                    bg = cols['sea'] if cell['neighbor'] == 0 else cols['sand']
                else:
                    bg = cols['sand']
                p.fillRect(rect, bg)
                
                # 数字描画
                if self.show_details and cell['neighbor'] > 0 and fs > 4:
                    if self.theme == 'Sea':
                        p.setPen(cols['text_base'])
                    else:
                        idx = cell['neighbor']
                        p.setPen(self.num_colors[idx] if idx < 8 else Qt.black)
                    p.drawText(rect, Qt.AlignCenter, str(cell['neighbor']))
        else:
            # 未開放セル（陸地）
            p.fillRect(rect, cols['land'])
            if self.show_details and cell['flagged'] and fs > 4:
                p.setPen(Qt.red)
                p.drawText(rect, Qt.AlignCenter, "🚩")

    def draw_classic(self, p, x, y, s, cell, cols, fs):
        """クラシックモード（立体的）の描画"""
        rect = QRect(x, y, s, s)
        if cell['revealed']:
            p.fillRect(rect, cols['sand'])
            p.setPen(QPen(QColor('gray'), 1))
            p.drawRect(x, y, s, s) # へこんだ枠線
            if cell['is_mine']:
                p.fillRect(QRect(x+1, y+1, s-2, s-2), cols['mine_bg'])
                if self.show_details and fs > 4:
                    p.setPen(Qt.black)
                    p.drawText(rect, Qt.AlignCenter, "*")
            elif self.show_details and cell['neighbor'] > 0 and fs > 4:
                idx = cell['neighbor']
                p.setPen(self.num_colors[idx] if idx < 8 else Qt.black)
                p.drawText(rect, Qt.AlignCenter, str(cell['neighbor']))
        else:
            p.fillRect(rect, cols['land'])
            # 3Dベベル（出っ張り）表現
            p.fillRect(x, y, s, 2, Qt.white)      # 上ハイライト
            p.fillRect(x, y, 2, s, Qt.white)      # 左ハイライト
            p.fillRect(x, y+s-2, s, 2, Qt.darkGray) # 下シャドウ
            p.fillRect(x+s-2, y, 2, s, Qt.darkGray) # 右シャドウ
            if self.show_details and cell['flagged'] and fs > 4:
                p.setPen(Qt.red)
                p.drawText(rect, Qt.AlignCenter, "P")

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        old_zoom = self.zoom
        if delta > 0:
            self.zoom = min(self.zoom * 1.15, 20.0)
        else:
            self.zoom = max(self.zoom / 1.15, 0.1)
        # ズーム中心をマウス位置に
        mx = event.position().x()
        my = event.position().y()
        ratio = self.zoom / old_zoom
        self.pan_x = int(mx - ratio * (mx - self.pan_x))
        self.pan_y = int(my - ratio * (my - self.pan_y))
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton or event.button() == Qt.RightButton:
            self._dragging = True
            self._drag_start = (event.position().x() - self.pan_x, event.position().y() - self.pan_y)
            return
        if self.parent_logic and event.button() == Qt.LeftButton:
            x = int((event.position().x() - self.offset_x) // self.cell_size)
            y = int((event.position().y() - self.offset_y) // self.cell_size)
            if 0 <= x < self.grid_w and 0 <= y < self.grid_h:
                self.parent_logic.on_cell_clicked(x, y)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start:
            self.pan_x = int(event.position().x() - self._drag_start[0])
            self.pan_y = int(event.position().y() - self._drag_start[1])
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton or event.button() == Qt.RightButton:
            self._dragging = False
            self._drag_start = None

# ==========================================
# メインウィンドウ (ゲームロジック)
# ==========================================
class LuckSweeperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LuckSweeper")
        self.resize(1200, 750)
        
        self.current_lang = 'jp'
        self.sound_manager = SoundManager()
        
        # ゲームステート初期値
        self.grid_w = 20
        self.grid_h = 20
        self.bomb_ratio = 0.15
        self.bot_delay = 100
        self.bot_strategy = 'Island' # ボットの戦略
        self.game_over = False
        self.is_thinking = False
        self.num_mines = 0
        
        self.init_ui()
        
        # 起動直後にゲームを開始
        QTimer.singleShot(100, self.restart_game)
        self.update_texts() # 言語反映

    def init_ui(self):
        """UIコンポーネントの配置"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左側：ゲーム盤面
        self.board_view = BoardWidget()
        self.board_view.parent_logic = self
        layout.addWidget(self.board_view, stretch=1) # 伸縮可能にする
        
        # 右側：タブパネル
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(300)
        # タブのスタイルシート設定
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; background: #f5f5f5; }
            QTabBar::tab { background: #ddd; padding: 8px 20px; border-bottom: 2px solid #ccc; }
            QTabBar::tab:selected { background: #f5f5f5; border-bottom: 2px solid #3498db; }
        """)
        layout.addWidget(self.tabs)
        
        # --- タブ1: メイン設定 ---
        self.tab_main = QWidget()
        self.tabs.addTab(self.tab_main, "")
        ml = QVBoxLayout(self.tab_main)
        ml.setSpacing(15)
        ml.setContentsMargins(20, 20, 20, 20)
        
        # 言語切替ボタン
        self.btn_lang = QPushButton("English")
        self.btn_lang.setCursor(Qt.PointingHandCursor)
        self.btn_lang.clicked.connect(self.toggle_language)
        ml.addWidget(self.btn_lang)

        # ゲーム設定グループ（幅・高さ・爆弾）
        self.grp_game = QGroupBox()
        gl = QVBoxLayout(self.grp_game)
        self.tf_w = self.create_input(gl, "lbl_w", 20)
        self.tf_h = self.create_input(gl, "lbl_h", 20)
        self.tf_b = self.create_input(gl, "lbl_b", 15)
        ml.addWidget(self.grp_game)
        
        # 表示設定グループ
        self.grp_vis = QGroupBox()
        vl = QVBoxLayout(self.grp_vis)
        self.lbl_theme = QLabel()
        vl.addWidget(self.lbl_theme)
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Modern", "Sea", "Classic", "Brazil", "Hoover", "Retro", "Sakura", "Arctic", "Sunset", "Hacker"])
        self.combo_theme.currentTextChanged.connect(self.change_theme)
        vl.addWidget(self.combo_theme)
        self.chk_detail = QCheckBox()
        self.chk_detail.setChecked(True)
        self.chk_detail.toggled.connect(self.toggle_details)
        vl.addWidget(self.chk_detail)
        ml.addWidget(self.grp_vis)
        
        # ボット設定グループ
        self.grp_bot = QGroupBox()
        bl = QVBoxLayout(self.grp_bot)
        self.lbl_style = QLabel()
        bl.addWidget(self.lbl_style)
        self.combo_style = QComboBox()
        self.combo_style.addItems(["Island", "Standard"]) 
        self.combo_style.currentTextChanged.connect(self.change_style)
        bl.addWidget(self.combo_style)
        
        self.lbl_speed = QLabel()
        bl.addWidget(self.lbl_speed)
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(1, 800)
        self.slider_speed.setValue(self.bot_delay)
        self.slider_speed.setInvertedAppearance(True) # 左＝遅い、右＝速い（delay小）に見せるため反転
        self.slider_speed.valueChanged.connect(self.change_speed)
        bl.addWidget(self.slider_speed)
        ml.addWidget(self.grp_bot)
        
        # リセットボタン
        self.btn_reset = QPushButton()
        self.btn_reset.setStyleSheet("background-color: #2c3e50; color: white; padding: 15px; font-weight: bold; border-radius: 5px;")
        self.btn_reset.clicked.connect(self.restart_game)
        ml.addWidget(self.btn_reset)
        
        # エラー表示ラベル
        self.lbl_error = QLabel()
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")
        self.lbl_error.hide()
        ml.addWidget(self.lbl_error)

        ml.addStretch()

        # 爆弾残数表示
        self.lbl_mines = QLabel()
        self.lbl_mines.setAlignment(Qt.AlignCenter)
        self.lbl_mines.setStyleSheet("padding: 5px; font-size: 13px;")
        ml.addWidget(self.lbl_mines)

        # ステータスバー
        self.status_bar = QLabel()
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setWordWrap(True)
        self.status_bar.setStyleSheet("background-color: #e0e0e0; padding: 10px; border-radius: 5px; color: #333;")
        ml.addWidget(self.status_bar)

        # --- タブ2: 機能調整 ---
        self.tab_feat = QWidget()
        self.tabs.addTab(self.tab_feat, "")
        fl = QVBoxLayout(self.tab_feat)
        fl.setSpacing(20)
        
        # アニメーション調整
        self.grp_anim = QGroupBox()
        al = QVBoxLayout(self.grp_anim)
        self.tf_overlay_dur = self.create_input(al, "lbl_overlay_dur", 500)
        self.tf_overlay_alpha = self.create_input(al, "lbl_overlay_alpha", 200)
        fl.addWidget(self.grp_anim)
        
        # システム設定（音）
        self.grp_sys = QGroupBox()
        sl = QVBoxLayout(self.grp_sys)
        self.chk_sound = QCheckBox()
        self.chk_sound.setChecked(True)
        self.chk_sound.toggled.connect(self.toggle_sound)
        sl.addWidget(self.chk_sound)
        fl.addWidget(self.grp_sys)
        
        fl.addStretch()
        
        # --- タブ3: 説明 ---
        self.tab_about = QWidget()
        self.tabs.addTab(self.tab_about, "")
        ab_l = QVBoxLayout(self.tab_about)
        self.txt_about = QTextEdit()
        self.txt_about.setReadOnly(True)
        self.txt_about.setStyleSheet("background: transparent; border: none;")
        ab_l.addWidget(self.txt_about)

    def create_input(self, layout, text_key, default_val):
        """ラベルと入力欄のセットを作成するヘルパー関数"""
        row = QHBoxLayout()
        lbl = QLabel()
        lbl.setProperty('key', text_key) # 言語切り替え用にキーを保持
        tf = QLineEdit(str(default_val))
        tf.setAlignment(Qt.AlignCenter)
        row.addWidget(lbl)
        row.addWidget(tf)
        layout.addLayout(row)
        if not hasattr(self, 'dynamic_labels'): self.dynamic_labels = []
        self.dynamic_labels.append(lbl)
        return tf

    def toggle_language(self):
        """日本語/英語の切り替え"""
        self.current_lang = 'en' if self.current_lang == 'jp' else 'jp'
        self.update_texts()

    def update_texts(self):
        """現在の言語設定に合わせてUIのテキストを更新"""
        t = TEXTS[self.current_lang]
        
        self.tabs.setTabText(0, t['tab_main'])
        self.tabs.setTabText(1, t['tab_feat'])
        self.tabs.setTabText(2, t['tab_about'])
        self.btn_lang.setText(t['lang_btn'])
        self.grp_game.setTitle(t['grp_game'])
        self.grp_vis.setTitle(t['grp_vis'])
        self.grp_bot.setTitle(t['grp_bot'])
        self.grp_anim.setTitle(t['feat_anim'])
        self.grp_sys.setTitle(t['feat_sys'])
        
        self.lbl_theme.setText(t['lbl_theme'])
        self.chk_detail.setText(t['chk_detail'])
        self.lbl_style.setText(t['lbl_style'])
        
        # コンボボックスの中身も更新（選択位置は維持）
        idx = self.combo_style.currentIndex()
        self.combo_style.blockSignals(True)
        self.combo_style.clear()
        self.combo_style.addItems([t['style_island'], t['style_std']])
        self.combo_style.setCurrentIndex(idx)
        self.combo_style.blockSignals(False)
        
        self.lbl_speed.setText(f"{t['lbl_speed']} {self.bot_delay}ms")
        self.btn_reset.setText(t['btn_reset'])
        self.chk_sound.setText(t['chk_sound'])
        
        self.txt_about.setHtml(t['about_text'])
        
        # 動的に生成したラベルの更新
        for lbl in self.dynamic_labels:
            key = lbl.property('key')
            if key and key in t:
                lbl.setText(t[key])
                
        # ステータスバーの更新（ゲーム進行状況によって分岐）
        if self.game_over:
            pass # ゲームオーバー時のテキストはそのまま
        elif self.is_thinking:
            self.status_bar.setText(t['status_ai'])
        else:
            self.status_bar.setText(t['status_human'])

    # --- UIイベントハンドラ ---
    def change_theme(self, text):
        self.board_view.theme = text
        self.board_view.update()

    def toggle_details(self, checked):
        self.board_view.show_details = checked
        self.board_view.update()

    def toggle_sound(self, checked):
        self.sound_manager.muted = not checked

    def change_style(self, text):
        idx = self.combo_style.currentIndex()
        self.bot_strategy = 'Island' if idx == 0 else 'Standard'

    def change_speed(self, val):
        self.bot_delay = val
        t = TEXTS[self.current_lang]
        self.lbl_speed.setText(f"{t['lbl_speed']} {val}ms")

    def update_status(self, mode):
        """ステータスバーの色と文字を更新"""
        t = TEXTS[self.current_lang]
        s = self.status_bar
        if mode == 'ai':
            s.setText(t['status_ai'])
            s.setStyleSheet("background-color: #3498db; color: white; padding: 10px; border-radius: 5px;")
        elif mode == 'human':
            s.setText(t['status_human'])
            s.setStyleSheet("background-color: #f1c40f; color: black; padding: 10px; border-radius: 5px;")
        elif mode == 'ready':
            s.setText(t['status_ready'])
            s.setStyleSheet("background-color: #2ecc71; color: white; padding: 10px; border-radius: 5px;")
        elif mode == 'win':
            s.setText(t['status_win'])
            s.setStyleSheet("background-color: white; color: black; border: 2px solid #2ecc71; padding: 10px; border-radius: 5px;")
        elif mode == 'lose':
            s.setText(t['status_lose'])
            s.setStyleSheet("background-color: black; color: red; padding: 10px; border-radius: 5px;")

    def generate_island_mines(self, total, mines_to_place):
        """
        【重要】海モード専用: 爆弾を島状に配置するアルゴリズム (難易度調整版)
        完全ランダムではなく、既存の爆弾の隣に新しい爆弾を置く確率を高めることで「島」を作る。
        ただし、あまりに密集すると難易度が高すぎるため、適度にバラけさせる調整を入れている。
        """
        if mines_to_place >= total: return list(range(total))
        
        w, h = self.grid_w, self.grid_h
        mine_set = set()
        
        # 1. 最初の「種（シード）」を撒く
        # 種の数が多いほど、島が分散して「諸島」になり、隙間ができやすくなる（難易度緩和）
        seeds = max(3, mines_to_place // 5)
        
        for _ in range(seeds):
            while True:
                idx = random.randint(0, total - 1)
                if idx not in mine_set:
                    mine_set.add(idx)
                    break
        
        # 2. 残りの爆弾を配置
        attempts = 0
        while len(mine_set) < mines_to_place and attempts < total * 10:
            attempts += 1
            
            # 結合確率: 80%なら隣にくっつく、20%なら離れた場所に飛ぶ
            # 以前の93%から下げて、隙間を作りやすくした
            grow_island = (random.random() < 0.80)
            
            if grow_island and mine_set:
                # 既存の爆弾をランダムに選び、その周囲8方向に増殖を試みる
                src_idx = random.choice(list(mine_set))
                sx, sy = src_idx % w, src_idx // w
                
                dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)])
                nx, ny = sx + dx, sy + dy
                
                if 0 <= nx < w and 0 <= ny < h:
                    n_idx = ny * w + nx
                    mine_set.add(n_idx)
            else:
                # 完全ランダム配置（飛地を作る）
                idx = random.randint(0, total - 1)
                mine_set.add(idx)
                
        return list(mine_set)

    def restart_game(self):
        """ゲームのリセット・開始処理"""
        self.lbl_error.hide()
        # メイン設定の読み込み
        try:
            w = int(self.tf_w.text())
            h = int(self.tf_h.text())
            b = int(self.tf_b.text())
            errors = []
            if w < 2 or w > 200:
                errors.append(f"幅は2〜200 (入力: {w})")
            if h < 2 or h > 200:
                errors.append(f"高さは2〜200 (入力: {h})")
            if b < 1 or b > 99:
                errors.append(f"爆弾%は1〜99 (入力: {b})")
            if errors:
                self.lbl_error.setText('\n'.join(errors))
                self.lbl_error.show()
                return
            self.grid_w = w
            self.grid_h = h
            self.bomb_ratio = b / 100.0
        except ValueError:
            self.lbl_error.setText("数値を入力してください")
            self.lbl_error.show()
            return
        
        # 機能設定の読み込み
        try:
            dur = int(self.tf_overlay_dur.text())
            alpha = int(self.tf_overlay_alpha.text())
            self.board_view.overlay_anim_duration = max(100, dur)
            self.board_view.overlay_alpha_max = max(0, min(alpha, 255))
        except: pass

        # 状態リセット
        self.game_over = False
        self.is_thinking = False
        self.first_click = True
        self.board_view.hide_overlay()
        self.board_view.zoom = 1.0
        self.board_view.pan_x = 0
        self.board_view.pan_y = 0
        self.board_view.set_grid_size(self.grid_w, self.grid_h)
        
        # 盤面データの初期化
        self.board_view.cells = [[{'is_mine': False, 'revealed': False, 'flagged': False, 'neighbor': 0} for _ in range(self.grid_w)] for _ in range(self.grid_h)]
            
        total = self.grid_w * self.grid_h
        self.num_mines = max(1, int(total * self.bomb_ratio))
        
        # --- 爆弾配置ロジックの分岐 ---
        if self.board_view.theme == 'Sea':
            # 海モードなら島生成アルゴリズムを使用
            indices = self.generate_island_mines(total, self.num_mines)
        else:
            # それ以外は完全ランダム
            indices = random.sample(range(total), self.num_mines)

        for i in indices:
            self.board_view.cells[i//self.grid_w][i%self.grid_w]['is_mine'] = True
            
        # 隣接する爆弾の数を計算
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                if not self.board_view.cells[y][x]['is_mine']:
                    c = 0
                    for dy in [-1,0,1]:
                        for dx in [-1,0,1]:
                            if dx==0 and dy==0: continue
                            nx,ny = x+dx, y+dy
                            if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                                if self.board_view.cells[ny][nx]['is_mine']: c+=1
                    self.board_view.cells[y][x]['neighbor'] = c
                    
        self.update_status('ready')
        self.update_mine_count()
        self.board_view.update()

    def ensure_safe_first_click(self, cx, cy):
        """初手安全保証: クリック位置とその周囲から地雷を移動"""
        cells = self.board_view.cells
        safe_zone = set()
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = cx+dx, cy+dy
                if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                    safe_zone.add((nx, ny))

        moved = []
        for (sx, sy) in safe_zone:
            if cells[sy][sx]['is_mine']:
                cells[sy][sx]['is_mine'] = False
                moved.append((sx, sy))

        for _ in moved:
            while True:
                rx = random.randint(0, self.grid_w-1)
                ry = random.randint(0, self.grid_h-1)
                if (rx,ry) not in safe_zone and not cells[ry][rx]['is_mine']:
                    cells[ry][rx]['is_mine'] = True
                    break

        if moved:
            for y in range(self.grid_h):
                for x in range(self.grid_w):
                    if not cells[y][x]['is_mine']:
                        c = 0
                        for dy in [-1,0,1]:
                            for dx in [-1,0,1]:
                                if dx==0 and dy==0: continue
                                nx,ny = x+dx,y+dy
                                if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                                    if cells[ny][nx]['is_mine']: c+=1
                        cells[y][x]['neighbor'] = c

    def on_cell_clicked(self, cx, cy):
        """セルがクリックされた時の処理"""
        if self.game_over:
            self.restart_game()
            return
        if self.is_thinking: return

        cell = self.board_view.cells[cy][cx]
        if cell['revealed'] or cell['flagged']: return

        if self.first_click:
            self.first_click = False
            self.ensure_safe_first_click(cx, cy)
            cell = self.board_view.cells[cy][cx]

        if cell['is_mine']:
            cell['revealed'] = True
            self.game_over_seq(False)
        else:
            # 安全 -> 再帰的に開く
            self.reveal_recursive(cx, cy)
            self.board_view.update()
            self.check_win()
            if not self.game_over:
                # ボットのターンへ移行
                self.is_thinking = True
                self.update_status('ai')
                QTimer.singleShot(self.bot_delay, self.auto_step)

    def reveal_recursive(self, x, y):
        """空白マスの連鎖オープン（スタックベース）"""
        cells = self.board_view.cells
        cell = cells[y][x]
        if cell['revealed']: return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            c = cells[cy][cx]
            if c['revealed']: continue
            c['revealed'] = True
            if c['neighbor'] == 0:
                for dy in [-1,0,1]:
                    for dx in [-1,0,1]:
                        if dx==0 and dy==0: continue
                        nx,ny = cx+dx, cy+dy
                        if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                            if not cells[ny][nx]['revealed']:
                                stack.append((nx,ny))

    def update_mine_count(self):
        """爆弾残数（地雷数 - フラグ数）を表示"""
        flag_count = sum(c['flagged'] for r in self.board_view.cells for c in r)
        self.lbl_mines.setText(f"💣 : {flag_count}/{self.num_mines}")

    def set_flag(self, x, y):
        """ボットがフラグを立てる処理"""
        cell = self.board_view.cells[y][x]
        if cell['revealed'] or cell['flagged']: return
        cell['flagged'] = True
        self.update_mine_count()
        self.check_flags_completion()
        self.board_view.update()

    def check_flags_completion(self):
        """フラグ数が爆弾数に達したか確認し、すべて正解ならクリア"""
        flag_count = sum(c['flagged'] for r in self.board_view.cells for c in r)
        if flag_count >= self.num_mines:
            all_ok = True
            for r in self.board_view.cells:
                for c in r:
                    # フラグ位置 != 爆弾位置 なら不正解
                    if c['flagged'] != c['is_mine']:
                        all_ok = False; break
            if all_ok: self.game_over_seq(True)
            else: self.game_over_seq(False)

    def check_win(self):
        """すべての安全マスが開けられたかチェック"""
        h = sum(1 for r in self.board_view.cells for c in r if not c['revealed'] and not c['is_mine'])
        if h == 0: self.game_over_seq(True)

    def get_constraints(self):
        """盤面から制約リストを生成: (残り地雷数, 未開放セル集合) のリスト"""
        constraints = []
        cells = self.board_view.cells
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                c = cells[y][x]
                if c['revealed'] and c['neighbor'] > 0:
                    unk = set()
                    flg = 0
                    for dy in [-1,0,1]:
                        for dx in [-1,0,1]:
                            if dx==0 and dy==0: continue
                            nx,ny = x+dx,y+dy
                            if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                                nc = cells[ny][nx]
                                if nc['flagged']: flg+=1
                                elif not nc['revealed']: unk.add((nx,ny))
                    if unk:
                        remaining = c['neighbor'] - flg
                        if remaining >= 0:
                            constraints.append((remaining, unk))
        return constraints

    def solve_basic(self, constraints):
        """基本制約: 単一セルの論理で確定するセルを返す"""
        safe = set()
        mines = set()
        for remaining, unk in constraints:
            if remaining == 0:
                safe |= unk
            elif remaining == len(unk):
                mines |= unk
        return safe, mines

    def solve_subset(self, constraints):
        """サブセット制約解析: 2つの制約間の包含関係から推論"""
        safe = set()
        mines = set()
        for i in range(len(constraints)):
            ri, si = constraints[i]
            for j in range(len(constraints)):
                if i == j: continue
                rj, sj = constraints[j]
                if si <= sj:
                    diff = sj - si
                    rdiff = rj - ri
                    if rdiff == 0:
                        safe |= diff
                    elif rdiff == len(diff):
                        mines |= diff
        return safe, mines

    def get_frontier_cells(self):
        """フロンティア（数字セルに隣接する未開放セル）を取得"""
        cells = self.board_view.cells
        frontier = set()
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                c = cells[y][x]
                if not c['revealed'] and not c['flagged']:
                    for dy in [-1,0,1]:
                        for dx in [-1,0,1]:
                            if dx==0 and dy==0: continue
                            nx,ny = x+dx,y+dy
                            if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                                nc = cells[ny][nx]
                                if nc['revealed'] and nc['neighbor'] > 0:
                                    frontier.add((x,y))
                                    break
                        else:
                            continue
                        break
        return frontier

    def solve_csp(self, constraints):
        """CSPバックトラッキングソルバー: フロンティアの全有効配置を列挙して確定セルを発見"""
        frontier = self.get_frontier_cells()
        if not frontier or len(frontier) > 25:
            return set(), set(), {}

        frontier_list = sorted(frontier)
        cell_idx = {cell: i for i, cell in enumerate(frontier_list)}

        relevant = []
        for remaining, unk in constraints:
            filtered = unk & frontier
            if filtered:
                indices = frozenset(cell_idx[c] for c in filtered)
                relevant.append((remaining, indices))

        n = len(frontier_list)
        mine_count = [0] * n
        total_configs = 0

        def backtrack(pos, assignment):
            nonlocal total_configs
            for rem, indices in relevant:
                assigned_mines = sum(1 for i in indices if i < pos and assignment[i])
                remaining_in_constraint = sum(1 for i in indices if i >= pos)
                assigned_safe = sum(1 for i in indices if i < pos and not assignment[i])
                total_in_constraint = len(indices)
                if assigned_mines > rem:
                    return
                if rem - assigned_mines > remaining_in_constraint:
                    return

            if pos == n:
                for rem, indices in relevant:
                    if sum(assignment[i] for i in indices) != rem:
                        return
                total_configs += 1
                for i in range(n):
                    if assignment[i]:
                        mine_count[i] += 1
                return

            assignment[pos] = False
            backtrack(pos + 1, assignment)
            assignment[pos] = True
            backtrack(pos + 1, assignment)

        assignment = [False] * n
        backtrack(0, assignment)

        safe = set()
        mines_set = set()
        probabilities = {}

        if total_configs > 0:
            for i in range(n):
                prob = mine_count[i] / total_configs
                probabilities[frontier_list[i]] = prob
                if mine_count[i] == 0:
                    safe.add(frontier_list[i])
                elif mine_count[i] == total_configs:
                    mines_set.add(frontier_list[i])

        return safe, mines_set, probabilities

    def auto_step(self):
        """ボットの思考ルーチン（3段階ソルバー + 確率推測）"""
        if self.game_over: return

        constraints = self.get_constraints()

        # Stage 1: 基本制約
        safe, mines = self.solve_basic(constraints)

        # Stage 2: サブセット制約解析
        if not safe and not mines:
            safe, mines = self.solve_subset(constraints)

        # Stage 3: CSPソルバー
        probabilities = {}
        if not safe and not mines:
            safe, mines, probabilities = self.solve_csp(constraints)

        # フラグ処理
        for (mx, my) in mines:
            self.set_flag(mx, my)

        # 安全セルを開く
        for (sx, sy) in safe:
            cell = self.board_view.cells[sy][sx]
            if not cell['revealed'] and not cell['flagged']:
                self.reveal_recursive(sx, sy)

        if safe or mines:
            self.board_view.update()
            self.check_win()
            if not self.game_over:
                QTimer.singleShot(self.bot_delay, self.auto_step)
            return

        # Stage 4: 確率ベース推測
        if probabilities:
            best_cell = min(probabilities, key=probabilities.get)
            prob = probabilities[best_cell]
            bx, by = best_cell
            cell = self.board_view.cells[by][bx]
            if not cell['revealed'] and not cell['flagged']:
                if prob >= 1.0:
                    self.set_flag(bx, by)
                else:
                    self.reveal_recursive(bx, by)
                self.board_view.update()
                self.check_win()
                if not self.game_over:
                    QTimer.singleShot(self.bot_delay, self.auto_step)
                return

        # フロンティア外の未開放セルがあれば最も孤立したものを選ぶ
        cells = self.board_view.cells
        frontier = self.get_frontier_cells()
        non_frontier = []
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                c = cells[y][x]
                if not c['revealed'] and not c['flagged'] and (x,y) not in frontier:
                    non_frontier.append((x,y))

        if non_frontier:
            choice = random.choice(non_frontier)
            self.reveal_recursive(choice[0], choice[1])
            self.board_view.update()
            self.check_win()
            if not self.game_over:
                QTimer.singleShot(self.bot_delay, self.auto_step)
            return

        # 手詰まり → 人間にパス
        self.is_thinking = False
        self.update_status('human')
        self.board_view.update()

    def count_revealed_neighbors(self, x, y):
        """周囲の「開放済みマス（海）」の数を数える。多いほど「角」や「半島」である可能性が高い"""
        c = 0
        for dy in [-1,0,1]:
            for dx in [-1,0,1]:
                if dx==0 and dy==0: continue
                nx, ny = x+dx, y+dy
                if 0<=nx<self.grid_w and 0<=ny<self.grid_h:
                    if self.board_view.cells[ny][nx]['revealed']: c+=1
        return c

    def game_over_seq(self, win):
        """ゲーム終了処理（勝敗判定と演出）"""
        if self.game_over: return
        self.game_over = True
        self.board_view.update()
        if win:
            self.sound_manager.play('win')
            self.update_status('win')
            self.board_view.show_overlay("MISSION PASSED", "#f1c40f") # 金色
        else:
            self.sound_manager.play('lose')
            self.update_status('lose')
            # 負けた時はすべての爆弾を表示
            for r in self.board_view.cells:
                for c in r:
                    if c['is_mine']: c['revealed'] = True
            self.board_view.update()
            self.board_view.show_overlay("WASTED", "#e74c3c") # 赤色

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = LuckSweeperWindow()
    w.show()
    sys.exit(app.exec())
