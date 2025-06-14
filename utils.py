"""
BeethovenLab - ユーティリティモジュール
楽譜の可視化、MIDI/MusicXML変換、分析結果の表示など
共通で使用する便利な関数群
"""

import music21 as m21
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional, Union
import tempfile
import os
import base64
from io import BytesIO
import json
from datetime import datetime

class MusicVisualizer:
    """楽譜と音楽データの可視化"""
    
    @staticmethod
    def create_piano_roll(score: m21.stream.Score, 
                         title: str = "Piano Roll") -> plt.Figure:
        """ピアノロール表示を作成"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 全ての音符を収集
        notes = []
        for part in score.parts:
            for element in part.flatten():
                if isinstance(element, m21.note.Note):
                    notes.append({
                        'pitch': element.pitch.midi,
                        'start': element.offset,
                        'duration': element.quarterLength,
                        'velocity': element.volume.velocity if element.volume.velocity else 64
                    })
                elif isinstance(element, m21.chord.Chord):
                    for pitch in element.pitches:
                        notes.append({
                            'pitch': pitch.midi,
                            'start': element.offset,
                            'duration': element.quarterLength,
                            'velocity': element.volume.velocity if element.volume.velocity else 64
                        })
        
        # ピアノロールをプロット
        for note in notes:
            # 音の高さに応じて色を変える
            color_intensity = note['velocity'] / 127.0
            ax.barh(
                note['pitch'], 
                note['duration'], 
                left=note['start'],
                height=0.8,
                color=plt.cm.viridis(color_intensity),
                edgecolor='black',
                linewidth=0.5
            )
        
        # グリッドと軸の設定
        ax.set_xlabel('Time (Quarter Notes)')
        ax.set_ylabel('MIDI Pitch')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        # Y軸にピアノの鍵盤名を表示
        if notes:
            min_pitch = min(n['pitch'] for n in notes)
            max_pitch = max(n['pitch'] for n in notes)
            
            # 主要な音高にラベルを付ける
            major_pitches = range(
                (min_pitch // 12) * 12,
                ((max_pitch // 12) + 1) * 12 + 1,
                12
            )
            pitch_labels = []
            pitch_positions = []
            
            for pitch in major_pitches:
                if min_pitch <= pitch <= max_pitch:
                    pitch_positions.append(pitch)
                    note_name = m21.pitch.Pitch(pitch).nameWithOctave
                    pitch_labels.append(note_name)
            
            ax.set_yticks(pitch_positions)
            ax.set_yticklabels(pitch_labels)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_harmonic_analysis_chart(harmony_data: List[str]) -> plt.Figure:
        """和声進行の分析チャート"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # 和声進行の時系列
        ax1.plot(range(len(harmony_data)), harmony_data, 'o-', markersize=8)
        ax1.set_xlabel('Measure')
        ax1.set_ylabel('Chord')
        ax1.set_title('Harmonic Progression')
        ax1.grid(True, alpha=0.3)
        
        # 和音の頻度分析
        chord_counts = pd.Series(harmony_data).value_counts()
        chord_counts.plot(kind='bar', ax=ax2)
        ax2.set_xlabel('Chord')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Chord Frequency Distribution')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_dynamic_curve(score: m21.stream.Score) -> plt.Figure:
        """強弱曲線を作成"""
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # 強弱記号を収集
        dynamics_data = []
        for part in score.parts:
            for element in part.flatten():
                if isinstance(element, m21.dynamics.Dynamic):
                    dynamics_data.append({
                        'offset': element.offset,
                        'dynamic': element.value,
                        'velocity': element.volumeScalar
                    })
        
        if dynamics_data:
            offsets = [d['offset'] for d in dynamics_data]
            velocities = [d['velocity'] for d in dynamics_data]
            labels = [d['dynamic'] for d in dynamics_data]
            
            # 曲線を描画
            ax.plot(offsets, velocities, 'o-', markersize=10, linewidth=2)
            
            # ラベルを追加
            for i, (offset, velocity, label) in enumerate(zip(offsets, velocities, labels)):
                ax.annotate(
                    label,
                    (offset, velocity),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=12,
                    fontweight='bold'
                )
        
        ax.set_xlabel('Time (Quarter Notes)')
        ax.set_ylabel('Dynamic Level')
        ax.set_title('Dynamic Curve')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
        
        # 動的レベルの参照線
        dynamic_levels = {
            'ppp': 0.125, 'pp': 0.25, 'p': 0.375,
            'mp': 0.5, 'mf': 0.625, 'f': 0.75,
            'ff': 0.875, 'fff': 1.0
        }
        
        for name, level in dynamic_levels.items():
            ax.axhline(y=level, color='gray', linestyle='--', alpha=0.3)
            ax.text(ax.get_xlim()[1] * 0.98, level, name, 
                   verticalalignment='center', fontsize=8)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_structure_diagram(structure_plan: List[Dict]) -> plt.Figure:
        """楽曲構造の図を作成"""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        # カラーマップ
        section_colors = {
            'exposition': '#FF6B6B',
            'development': '#4ECDC4',
            'recapitulation': '#45B7D1',
            'introduction': '#96CEB4',
            'coda': '#FECA57'
        }
        
        current_x = 0
        
        for section in structure_plan:
            width = section['measures']
            parent = section.get('parent_section', 'other')
            color = section_colors.get(parent, '#95A5A6')
            
            # セクションを描画
            rect = plt.Rectangle(
                (current_x, 0), width, 1,
                facecolor=color,
                edgecolor='black',
                linewidth=2
            )
            ax.add_patch(rect)
            
            # ラベルを追加
            ax.text(
                current_x + width/2, 0.5,
                section['name'].replace('_', '\n'),
                ha='center', va='center',
                fontsize=10,
                fontweight='bold',
                wrap=True
            )
            
            # 調性情報を追加
            if 'key' in section:
                ax.text(
                    current_x + width/2, -0.2,
                    section['key'],
                    ha='center', va='center',
                    fontsize=8,
                    style='italic'
                )
            
            current_x += width
        
        ax.set_xlim(0, current_x)
        ax.set_ylim(-0.5, 1.5)
        ax.set_xlabel('Measures')
        ax.set_title('Musical Structure')
        ax.set_yticks([])
        
        # 凡例を追加
        legend_elements = []
        for section_type, color in section_colors.items():
            legend_elements.append(
                plt.Rectangle((0, 0), 1, 1, facecolor=color, 
                            edgecolor='black', label=section_type.title())
            )
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.tight_layout()
        return fig

class FileConverter:
    """ファイル形式の変換"""
    
    @staticmethod
    def score_to_midi(score: m21.stream.Score) -> bytes:
        """楽譜をMIDIバイトデータに変換"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as tmp:
            score.write('midi', fp=tmp.name)
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            midi_data = f.read()
        
        os.unlink(tmp_path)
        return midi_data
    
    @staticmethod
    def score_to_musicxml(score: m21.stream.Score) -> bytes:
        """楽譜をMusicXMLバイトデータに変換"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
            score.write('musicxml', fp=tmp.name)
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            xml_data = f.read()
        
        os.unlink(tmp_path)
        return xml_data
    
    @staticmethod
    def score_to_lilypond(score: m21.stream.Score) -> str:
    """楽譜をLilyPond形式に変換"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ly') as tmp:
            score.write('lily', fp=tmp.name)
            tmp_path = tmp.name
        
        with open(tmp_path, 'r', encoding='utf-8') as f:
            lily_data = f.read()
        
        os.unlink(tmp_path)
        return lily_data
        except Exception as e:
        # LilyPondが利用できない場合は代替テキストを返す
        return "% LilyPond is not available in this environment\n% Please install LilyPond to export in this format."
    
    @staticmethod
    def create_score_image(score: m21.stream.Score) -> Optional[bytes]:
        """楽譜の画像を作成（簡易版）"""
        try:
            # music21の内蔵機能を使用
            # 注：実際の使用にはLilyPondまたはMuseScoreが必要
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                score.write('lily.png', fp=tmp.name)
                tmp_path = tmp.name
            
            with open(tmp_path, 'rb') as f:
                image_data = f.read()
            
            os.unlink(tmp_path)
            return image_data
        except:
            # エラーの場合はNoneを返す
            return None

class AnalysisReporter:
    """分析結果のレポート生成"""
    
    @staticmethod
    def create_analysis_report(analysis_results: Dict) -> str:
        """分析結果の詳細レポートを作成"""
        report = f"""
# 🎼 BeethovenLab 楽曲分析レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 総合統計

"""
        
        # 和声分析
        if 'harmonic' in analysis_results:
            report += "### 🎵 和声分析\n\n"
            harmonic = analysis_results['harmonic']
            
            if 'progression_probabilities' in harmonic:
                report += "**主要な和声進行:**\n"
                for chord, next_chords in list(harmonic['progression_probabilities'].items())[:5]:
                    report += f"- {chord} → "
                    top_progressions = sorted(
                        next_chords.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:3]
                    report += ", ".join([f"{c} ({p:.1%})" for c, p in top_progressions])
                    report += "\n"
            
            report += "\n"
        
        # 旋律分析
        if 'melodic' in analysis_results:
            report += "### 🎼 旋律分析\n\n"
            melodic = analysis_results['melodic']
            
            if 'interval_distribution' in melodic:
                report += "**頻出音程:**\n"
                intervals = sorted(
                    melodic['interval_distribution'].items(),
                    key=lambda x: float(x[1]),
                    reverse=True
                )[:5]
                for interval, freq in intervals:
                    interval_name = AnalysisReporter._interval_name(int(interval))
                    report += f"- {interval_name}: {float(freq):.1%}\n"
            
            if 'contour_types' in melodic:
                report += "\n**旋律輪郭の分布:**\n"
                for contour, ratio in melodic['contour_types'].items():
                    report += f"- {contour}: {ratio:.1%}\n"
            
            report += "\n"
        
        # リズム分析
        if 'rhythmic' in analysis_results:
            report += "### 🥁 リズム分析\n\n"
            rhythmic = analysis_results['rhythmic']
            
            if 'common_patterns' in rhythmic:
                report += "**頻出リズムパターン:**\n"
                for i, pattern in enumerate(rhythmic['common_patterns'][:5]):
                    report += f"{i+1}. {AnalysisReporter._format_rhythm(pattern)}\n"
            
            if 'syncopation_rate' in rhythmic:
                report += f"\n**シンコペーション率:** {rhythmic['syncopation_rate']:.1%}\n"
            
            report += "\n"
        
        # 構造分析
        if 'structural' in analysis_results:
            report += "### 🏛️ 構造分析\n\n"
            structural = analysis_results['structural']
            
            if 'form' in structural:
                report += f"**楽曲形式:** {structural['form']}\n\n"
            
            if 'sections' in structural:
                report += "**セクション構成:**\n"
                for section in structural['sections']:
                    report += f"- {section['name']}: 第{section['start']}〜{section['end']}小節\n"
        
        return report
    
    @staticmethod
    def _interval_name(interval: int) -> str:
        """音程の名前を取得"""
        interval_names = {
            0: "同度", 1: "短2度", 2: "長2度", 3: "短3度", 4: "長3度",
            5: "完全4度", 6: "増4度/減5度", 7: "完全5度", 8: "短6度",
            9: "長6度", 10: "短7度", 11: "長7度", 12: "オクターブ"
        }
        
        if abs(interval) > 12:
            return f"{abs(interval)}半音"
        
        name = interval_names.get(abs(interval), f"{abs(interval)}半音")
        return f"上行{name}" if interval > 0 else f"下行{name}" if interval < 0 else name
    
    @staticmethod
    def _format_rhythm(pattern: List[float]) -> str:
        """リズムパターンを読みやすい形式に"""
        note_names = {
            4.0: "全音符",
            2.0: "2分音符",
            1.0: "4分音符",
            0.5: "8分音符",
            0.25: "16分音符",
            0.125: "32分音符"
        }
        
        formatted = []
        for duration in pattern:
            if duration in note_names:
                formatted.append(note_names[duration])
            else:
                formatted.append(f"{duration}拍")
        
        return " - ".join(formatted)

class StreamlitHelpers:
    """Streamlit用のヘルパー関数"""
    
    @staticmethod
    def display_score_info(score: m21.stream.Score):
        """楽譜の基本情報を表示"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_measures = sum(
                len(part.getElementsByClass('Measure')) 
                for part in score.parts
            ) // len(score.parts)
            st.metric("小節数", total_measures)
        
        with col2:
            st.metric("パート数", len(score.parts))
        
        with col3:
            duration = score.duration.quarterLength
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            st.metric("演奏時間", f"{minutes}:{seconds:02d}")
        
        with col4:
            # 最初のテンポマーク
            tempo_marks = list(score.flatten().getElementsByClass(m21.tempo.MetronomeMark))
            if tempo_marks:
                st.metric("テンポ", f"{tempo_marks[0].number} BPM")
            else:
                st.metric("テンポ", "120 BPM")
    
    @staticmethod
    def create_download_section(score: m21.stream.Score, 
                              base_filename: str = "beethoven_lab_composition"):
        """ダウンロードセクションを作成"""
        st.subheader("💾 ダウンロード")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # MIDI
            midi_data = FileConverter.score_to_midi(score)
            st.download_button(
                label="🎹 MIDI",
                data=midi_data,
                file_name=f"{base_filename}.mid",
                mime="audio/midi"
            )
        
        with col2:
            # MusicXML
            xml_data = FileConverter.score_to_musicxml(score)
            st.download_button(
                label="📄 MusicXML",
                data=xml_data,
                file_name=f"{base_filename}.xml",
                mime="application/vnd.recordare.musicxml+xml"
            )
        
        with col3:
            # LilyPond
            lily_data = FileConverter.score_to_lilypond(score)
            st.download_button(
                label="🎼 LilyPond",
                data=lily_data,
                file_name=f"{base_filename}.ly",
                mime="text/plain"
            )
    
    @staticmethod
    def display_generation_stats(generation_time: float, 
                               complexity_score: float):
        """生成統計を表示"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "生成時間",
                f"{generation_time:.1f}秒",
                delta=None,
                help="楽曲生成にかかった時間"
            )
        
        with col2:
            st.metric(
                "複雑度スコア",
                f"{complexity_score:.1f}/10",
                delta=None,
                help="生成された楽曲の複雑さ（10が最も複雑）"
            )
    
    @staticmethod
    def create_feedback_form():
        """フィードバックフォームを作成"""
        with st.expander("📝 フィードバック"):
            st.write("生成された楽曲についてのご意見をお聞かせください")
            
            quality = st.slider(
                "楽曲のクオリティ",
                min_value=1,
                max_value=5,
                value=3,
                help="1: 低い, 5: 高い"
            )
            
            beethoven_likeness = st.slider(
                "ベートーヴェンらしさ",
                min_value=1,
                max_value=5,
                value=3,
                help="1: 全く似ていない, 5: とても似ている"
            )
            
            comments = st.text_area(
                "コメント（任意）",
                placeholder="改善点や感想などをお聞かせください"
            )
            
            if st.button("フィードバックを送信"):
                # 実際のアプリケーションではここでフィードバックを保存
                st.success("フィードバックありがとうございました！")
                return {
                    'quality': quality,
                    'beethoven_likeness': beethoven_likeness,
                    'comments': comments,
                    'timestamp': datetime.now().isoformat()
                }
        
        return None

# 定数とユーティリティ
BEETHOVEN_PERIODS = {
    'early': '初期（1792-1802）',
    'middle': '中期（1803-1814）',
    'late': '後期（1815-1827）'
}

MUSICAL_FORMS = {
    'sonata': 'ソナタ形式',
    'rondo': 'ロンド形式',
    'theme_variations': '主題と変奏'
}

def get_beethoven_quote() -> str:
    """ベートーヴェンの名言をランダムに取得"""
    quotes = [
        "音楽は、人類の精神から炎を打ち出すべきだ。",
        "真の芸術家は自分が最高傑作だと思ったことは一度もない。",
        "音楽とは精神の中から現れる啓示である。",
        "困難な時にこそ、真の強さが試される。",
        "運命はこのように扉を叩く。"
    ]
    return np.random.choice(quotes)
