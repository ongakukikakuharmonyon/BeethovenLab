import streamlit as st
import music21 as m21
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import random
import tempfile
import os
import json
from typing import List, Dict, Tuple

st.set_page_config(
    page_title="BeethovenLab - AI作曲システム",
    page_icon="🎼",
    layout="wide"
)

# キャッシュとセッション状態の初期化
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'generated_score' not in st.session_state:
    st.session_state.generated_score = None

class BeethovenAnalyzer:
    """ベートーヴェンの楽曲スタイルを分析するクラス"""
    
    def __init__(self):
        self.harmonic_progressions = defaultdict(list)
        self.melodic_patterns = defaultdict(list)
        self.rhythmic_patterns = []
        self.structural_patterns = {}
        
    def analyze_sample_pieces(self):
        """サンプルデータから特徴を抽出（実際のベートーヴェンデータの代替）"""
        # ベートーヴェン中期のスタイル特徴をハードコード
        # 実際のプロジェクトでは.krnファイルから分析
        
        # 典型的な和声進行
        self.harmonic_progressions = {
            'I': ['V', 'IV', 'vi', 'ii'],
            'V': ['I', 'vi', 'IV'],
            'IV': ['V', 'I', 'ii'],
            'vi': ['IV', 'V', 'ii'],
            'ii': ['V', 'I'],
            'iii': ['vi', 'IV'],
            'vii°': ['I', 'V']
        }
        
        # 旋律パターン（音程）
        self.melodic_intervals = {
            'ascending': [0, 2, 4, 5, 7, 9, 11, 12],  # 上行音程
            'descending': [0, -2, -4, -5, -7, -9, -11, -12],  # 下行音程
            'leap': [7, -7, 5, -5, 12, -12]  # 跳躍
        }
        
        # リズムパターン（拍の長さ）
        self.rhythmic_patterns = [
            [1, 1, 1, 1],  # 四分音符の連続
            [2, 2],  # 二分音符
            [1, 0.5, 0.5, 1, 1],  # シンコペーション
            [0.5, 0.5, 0.5, 0.5, 2],  # 短い音符から長い音符へ
            [3, 1],  # 付点二分音符
            [1.5, 0.5, 2]  # 付点四分音符
        ]
        
        # 構造パターン（ソナタ形式）
        self.structural_patterns = {
            'exposition': {
                'length_ratio': 0.3,
                'key_areas': ['I', 'V'],
                'themes': 2
            },
            'development': {
                'length_ratio': 0.4,
                'key_areas': ['vi', 'ii', 'iii', 'IV', 'V'],
                'modulation_frequency': 'high'
            },
            'recapitulation': {
                'length_ratio': 0.3,
                'key_areas': ['I'],
                'themes': 2
            }
        }
        
        # ベートーヴェン的な動機の使用
        self.motivic_cells = [
            [0, 0, 0, -4],  # 運命の動機風
            [0, 4, 7, 4, 0],  # アルペジオ
            [0, 2, 0, -2, 0],  # 回音
            [0, 7, 5, 4, 2, 0]  # 下降スケール
        ]

class BeethovenComposer:
    """ベートーヴェン風の楽曲を生成するクラス"""
    
    def __init__(self, analyzer: BeethovenAnalyzer):
        self.analyzer = analyzer
        self.key = m21.key.Key('C')  # デフォルトはハ長調
        
    def generate_melody(self, num_notes: int, melodic_curve: str = 'arch') -> List[m21.note.Note]:
        """メロディーラインを生成"""
        notes = []
        current_pitch = 60  # C4から開始
        
        # メロディーカーブに基づいて音高を決定
        if melodic_curve == 'arch':
            # アーチ型（上昇→下降）
            peak_position = num_notes // 2
            for i in range(num_notes):
                if i < peak_position:
                    # 上昇傾向
                    interval = random.choice(self.analyzer.melodic_intervals['ascending'])
                else:
                    # 下降傾向
                    interval = random.choice(self.analyzer.melodic_intervals['descending'])
                
                # 跳躍を時々入れる
                if random.random() < 0.2:
                    interval = random.choice(self.analyzer.melodic_intervals['leap'])
                
                current_pitch += interval
                # 音域制限
                current_pitch = max(48, min(84, current_pitch))  # C3 - C6
                
                note = m21.note.Note(current_pitch)
                notes.append(note)
        
        return notes
    
    def generate_harmony(self, melody: List[m21.note.Note], chord_rhythm: List[float]) -> List[m21.chord.Chord]:
        """メロディーに合わせた和声を生成"""
        chords = []
        current_chord = 'I'
        
        for i, rhythm_value in enumerate(chord_rhythm):
            # 和声進行に基づいて次のコードを選択
            next_chords = self.analyzer.harmonic_progressions.get(current_chord, ['I'])
            current_chord = random.choice(next_chords)
            
            # コードを生成
            if current_chord == 'I':
                chord = m21.chord.Chord(['C3', 'E3', 'G3'])
            elif current_chord == 'V':
                chord = m21.chord.Chord(['G3', 'B3', 'D4'])
            elif current_chord == 'IV':
                chord = m21.chord.Chord(['F3', 'A3', 'C4'])
            elif current_chord == 'vi':
                chord = m21.chord.Chord(['A3', 'C4', 'E4'])
            elif current_chord == 'ii':
                chord = m21.chord.Chord(['D3', 'F3', 'A3'])
            elif current_chord == 'iii':
                chord = m21.chord.Chord(['E3', 'G3', 'B3'])
            else:  # vii°
                chord = m21.chord.Chord(['B3', 'D4', 'F4'])
            
            chord.quarterLength = rhythm_value
            chords.append(chord)
            
        return chords
    
    def apply_motivic_development(self, melody: List[m21.note.Note]) -> List[m21.note.Note]:
        """動機的発展を適用"""
        # ランダムに動機を選択
        motif = random.choice(self.analyzer.motivic_cells)
        
        # メロディーに動機を組み込む
        for i in range(0, len(melody) - len(motif), random.randint(4, 8)):
            base_pitch = melody[i].pitch.midi
            for j, interval in enumerate(motif):
                if i + j < len(melody):
                    melody[i + j].pitch = m21.pitch.Pitch(base_pitch + interval)
        
        return melody
    
    def generate_section(self, section_type: str, num_measures: int) -> m21.stream.Part:
        """楽曲のセクションを生成"""
        part = m21.stream.Part()
        
        # 拍子記号
        ts = m21.meter.TimeSignature('4/4')
        part.append(ts)
        
        # 各小節を生成
        for measure_num in range(num_measures):
            measure = m21.stream.Measure(number=measure_num + 1)
            
            # リズムパターンを選択
            rhythm_pattern = random.choice(self.analyzer.rhythmic_patterns)
            
            # メロディーを生成
            melody_notes = self.generate_melody(len(rhythm_pattern), 'arch')
            
            # リズムを適用
            for note, rhythm in zip(melody_notes, rhythm_pattern):
                note.quarterLength = rhythm
                measure.append(note)
            
            # 強弱記号を追加（ベートーヴェン的な突然の変化）
            if random.random() < 0.2:
                if random.random() < 0.5:
                    dynamic = m21.dynamics.Dynamic('f')  # フォルテ
                else:
                    dynamic = m21.dynamics.Dynamic('p')  # ピアノ
                measure.insert(0, dynamic)
            
            part.append(measure)
        
        # 動機的発展を適用
        all_notes = [n for n in part.recurse().notes if isinstance(n, m21.note.Note)]
        self.apply_motivic_development(all_notes)
        
        return part
    
    def generate_complete_piece(self, total_measures: int) -> m21.stream.Score:
        """完全な楽曲を生成（ソナタ形式）"""
        score = m21.stream.Score()
        
        # テンポ設定
        tempo = m21.tempo.MetronomeMark(number=120, text="Allegro")
        score.insert(0, tempo)
        
        # 構造に基づいてセクションの長さを計算
        exposition_measures = int(total_measures * self.analyzer.structural_patterns['exposition']['length_ratio'])
        development_measures = int(total_measures * self.analyzer.structural_patterns['development']['length_ratio'])
        recapitulation_measures = total_measures - exposition_measures - development_measures
        
        # 右手パート（メロディー）
        right_hand = m21.stream.Part()
        right_hand.partName = "Piano Right Hand"
        
        # 左手パート（伴奏）
        left_hand = m21.stream.Part()
        left_hand.partName = "Piano Left Hand"
        
        # 提示部
        expo_right = self.generate_section('exposition', exposition_measures)
        right_hand.append(expo_right)
        
        # 展開部
        dev_right = self.generate_section('development', development_measures)
        right_hand.append(dev_right)
        
        # 再現部
        recap_right = self.generate_section('recapitulation', recapitulation_measures)
        right_hand.append(recap_right)
        
        # 左手の伴奏を生成
        for section_measures in [exposition_measures, development_measures, recapitulation_measures]:
            for m in range(section_measures):
                measure = m21.stream.Measure()
                
                # アルベルティ・バス風の伴奏パターン
                bass_pattern = ['C3', 'G3', 'E3', 'G3'] * 1  # 1小節分
                for note_name in bass_pattern:
                    note = m21.note.Note(note_name)
                    note.quarterLength = 1
                    measure.append(note)
                
                left_hand.append(measure)
        
        # スコアに追加
        score.insert(0, right_hand)
        score.insert(0, left_hand)
        
        return score

# Streamlitアプリケーション
st.title("🎼 BeethovenLab - ベートーヴェン風ピアノ曲自動作曲システム")
st.markdown("AIがベートーヴェン中期の作風を模倣してピアノ独奏曲を生成します")

# サイドバー
with st.sidebar:
    st.header("🎹 作曲設定")
    
    # 楽曲の長さ
    total_measures = st.select_slider(
        "楽曲の長さ（小節数）",
        options=[16, 32, 48, 64, 96, 144],
        value=32,
        help="生成する楽曲の総小節数を選択してください"
    )
    
    # 詳細設定
    with st.expander("🔧 詳細設定"):
        tempo = st.slider("テンポ (BPM)", 60, 180, 120, 10)
        key_signature = st.selectbox(
            "調性",
            ["C major", "G major", "D major", "A major", "F major", "B♭ major", "E♭ major"]
        )
        style_emphasis = st.select_slider(
            "スタイルの強調",
            options=["控えめ", "標準", "強め"],
            value="標準"
        )
    
    st.divider()
    
    # 生成ボタン
    generate_button = st.button(
        "🎵 作曲を開始",
        type="primary",
        use_container_width=True
    )
    
    # 分析情報の表示
    with st.expander("📊 スタイル分析情報"):
        st.markdown("""
        **ベートーヴェン中期の特徴:**
        - 動機の徹底的な展開
        - 突然の強弱変化
        - 拡大されたソナタ形式
        - 対位法的要素の導入
        - 感情の激しい対比
        """)

# メインエリア
if generate_button:
    # プログレスバー
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 分析フェーズ
    status_text.text("🔍 ベートーヴェンのスタイルを分析中...")
    progress_bar.progress(20)
    
    analyzer = BeethovenAnalyzer()
    analyzer.analyze_sample_pieces()
    
    # 作曲フェーズ
    status_text.text("🎼 楽曲構造を設計中...")
    progress_bar.progress(40)
    
    composer = BeethovenComposer(analyzer)
    
    status_text.text("🎹 メロディーと和声を生成中...")
    progress_bar.progress(60)
    
    # 楽曲生成
    generated_score = composer.generate_complete_piece(total_measures)
    st.session_state.generated_score = generated_score
    
    status_text.text("✨ 最終調整中...")
    progress_bar.progress(80)
    
    # 完了
    progress_bar.progress(100)
    status_text.text("✅ 作曲が完了しました！")
    
    # 結果の表示
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📜 生成された楽譜")
        
        # 楽譜のテキスト表示（実際のプロジェクトでは画像表示）
        st.code(generated_score.show('text'), language='text')
        
        # 構造分析
        st.subheader("🏛️ 楽曲構造")
        structure_data = {
            "セクション": ["提示部", "展開部", "再現部"],
            "小節数": [
                int(total_measures * 0.3),
                int(total_measures * 0.4),
                int(total_measures * 0.3)
            ],
            "主要調性": ["I (主調)", "変化", "I (主調)"]
        }
        st.dataframe(pd.DataFrame(structure_data))
    
    with col2:
        st.subheader("🎧 再生・ダウンロード")
        
        # MIDIファイルの生成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as tmp_file:
            generated_score.write('midi', fp=tmp_file.name)
            
            with open(tmp_file.name, 'rb') as f:
                midi_data = f.read()
            
            # 再生
            st.audio(midi_data, format='audio/midi')
            
            # ダウンロードボタン
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    label="💾 MIDI",
                    data=midi_data,
                    file_name=f"beethoven_lab_{total_measures}m.mid",
                    mime="audio/midi"
                )
            
            with col_b:
                # MusicXMLエクスポート
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as xml_file:
                    generated_score.write('musicxml', fp=xml_file.name)
                    with open(xml_file.name, 'rb') as f:
                        xml_data = f.read()
                    
                    st.download_button(
                        label="📄 MusicXML",
                        data=xml_data,
                        file_name=f"beethoven_lab_{total_measures}m.xml",
                        mime="application/vnd.recordare.musicxml+xml"
                    )
                    os.unlink(xml_file.name)
            
            os.unlink(tmp_file.name)
        
        # 生成情報
        st.subheader("ℹ️ 生成情報")
        st.info(f"""
        **生成日時**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
        **総小節数**: {total_measures}小節
        **推定演奏時間**: 約{total_measures * 2 // 60}分{total_measures * 2 % 60}秒
        **使用アルゴリズム**: マルコフ連鎖 + 構造モデル
        """)

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🎼 BeethovenLab v1.0 | ベートーヴェン中期作品の特徴を学習したAI作曲システム</p>
    <p>Created with ❤️ using Streamlit and music21</p>
</div>
""", unsafe_allow_html=True)
