"""
BeethovenLab - データローダーモジュール
ベートーヴェンのピアノソナタデータ（.krn形式）の読み込みと前処理
GitHub上の公開データセットから楽曲を取得し、分析可能な形式に変換
"""

import music21 as m21
import requests
import json
import streamlit as st
from typing import List, Dict, Optional, Tuple
import tempfile
import os
from pathlib import Path
import pandas as pd
import re

class BeethovenDataLoader:
    """ベートーヴェンの楽曲データを管理するクラス"""
    
    def __init__(self):
        # ベートーヴェンのピアノソナタ情報
        self.sonata_catalog = self._create_sonata_catalog()
        self.loaded_scores = {}
        self.sample_data_url = "https://raw.githubusercontent.com/musedata/humdrum-beethoven-piano-sonatas/master/"
        
    def _create_sonata_catalog(self) -> Dict:
        """ベートーヴェンのピアノソナタカタログを作成"""
        catalog = {
            'opus2no1': {
                'title': 'Piano Sonata No.1 in F minor, Op.2 No.1',
                'period': 'early',
                'year': 1795,
                'movements': 4,
                'key': 'F minor'
            },
            'opus10no2': {
                'title': 'Piano Sonata No.6 in F major, Op.10 No.2',
                'period': 'early',
                'year': 1797,
                'movements': 3,
                'key': 'F major'
            },
            'opus13': {
                'title': 'Piano Sonata No.8 in C minor, Op.13 "Pathétique"',
                'period': 'early',
                'year': 1798,
                'movements': 3,
                'key': 'C minor'
            },
            'opus27no2': {
                'title': 'Piano Sonata No.14 in C# minor, Op.27 No.2 "Moonlight"',
                'period': 'middle',
                'year': 1801,
                'movements': 3,
                'key': 'C# minor'
            },
            'opus31no2': {
                'title': 'Piano Sonata No.17 in D minor, Op.31 No.2 "Tempest"',
                'period': 'middle',
                'year': 1802,
                'movements': 3,
                'key': 'D minor'
            },
            'opus53': {
                'title': 'Piano Sonata No.21 in C major, Op.53 "Waldstein"',
                'period': 'middle',
                'year': 1804,
                'movements': 2,
                'key': 'C major'
            },
            'opus57': {
                'title': 'Piano Sonata No.23 in F minor, Op.57 "Appassionata"',
                'period': 'middle',
                'year': 1805,
                'movements': 3,
                'key': 'F minor'
            },
            'opus81a': {
                'title': 'Piano Sonata No.26 in E♭ major, Op.81a "Les Adieux"',
                'period': 'middle',
                'year': 1810,
                'movements': 3,
                'key': 'E♭ major'
            },
            'opus106': {
                'title': 'Piano Sonata No.29 in B♭ major, Op.106 "Hammerklavier"',
                'period': 'late',
                'year': 1818,
                'movements': 4,
                'key': 'B♭ major'
            },
            'opus111': {
                'title': 'Piano Sonata No.32 in C minor, Op.111',
                'period': 'late',
                'year': 1822,
                'movements': 2,
                'key': 'C minor'
            }
        }
        return catalog
    
    def get_sample_beethoven_data(self) -> Dict:
        """サンプルのベートーヴェンデータを生成（実際のkrnファイルが利用できない場合）"""
        # 中期のベートーヴェンスタイルを模したサンプルデータ
        sample_scores = {}
        
        # ワルトシュタイン第1楽章風のサンプル
        waldstein_sample = m21.stream.Score()
        part = m21.stream.Part()
        
        # 特徴的な開始部分
        # 急速な繰り返し音（ベートーヴェン中期の特徴）
        for i in range(8):
            note = m21.note.Note('C4')
            note.quarterLength = 0.5
            part.append(note)
        
        # 跳躍を含むメロディー
        melody_notes = ['E4', 'G4', 'C5', 'G4', 'E4', 'C4', 'G3', 'C4']
        for pitch in melody_notes:
            note = m21.note.Note(pitch)
            note.quarterLength = 0.5
            part.append(note)
        
        waldstein_sample.append(part)
        sample_scores['waldstein_opening'] = waldstein_sample
        
        # 熱情第1楽章風のサンプル
        appassionata_sample = m21.stream.Score()
        part = m21.stream.Part()
        
        # 激しい下降アルペジオ（熱情の特徴）
        arpeggio_notes = ['F5', 'C5', 'A4', 'F4', 'C4', 'A3', 'F3']
        for pitch in arpeggio_notes:
            note = m21.note.Note(pitch)
            note.quarterLength = 0.25
            part.append(note)
        
        # 休符と突然のフォルテ
        rest = m21.note.Rest()
        rest.quarterLength = 1
        part.append(rest)
        
        # 強烈な和音
        chord = m21.chord.Chord(['F3', 'A3', 'C4', 'F4'])
        chord.quarterLength = 2
        chord.volume.velocity = 120  # フォルテシモ
        part.append(chord)
        
        appassionata_sample.append(part)
        sample_scores['appassionata_opening'] = appassionata_sample
        
        return sample_scores
    
    @st.cache_data
    def load_krn_from_github(self, opus_key: str, movement: int = 1) -> Optional[m21.stream.Score]:
        """GitHubからkrnファイルを読み込む（キャッシュ付き）"""
        try:
            # URLを構築
            filename = f"{opus_key}-{movement:02d}.krn"
            url = f"{self.sample_data_url}{opus_key}/{filename}"
            
            # ファイルをダウンロード
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # 一時ファイルに保存
                with tempfile.NamedTemporaryFile(mode='w', suffix='.krn', delete=False) as tmp:
                    tmp.write(response.text)
                    tmp_path = tmp.name
                
                # music21で解析
                score = m21.converter.parse(tmp_path)
                
                # 一時ファイルを削除
                os.unlink(tmp_path)
                
                return score
            else:
                st.warning(f"ファイルが見つかりません: {url}")
                return None
                
        except Exception as e:
            st.error(f"ファイルの読み込みエラー: {str(e)}")
            return None
    
    def load_middle_period_sonatas(self) -> Dict[str, m21.stream.Score]:
        """中期のソナタを読み込む"""
        middle_period_works = {
            k: v for k, v in self.sonata_catalog.items() 
            if v['period'] == 'middle'
        }
        
        loaded_scores = {}
        
        # 実際のデータ読み込みを試みる
        for opus_key, info in middle_period_works.items():
            score = self.load_krn_from_github(opus_key, movement=1)
            if score:
                loaded_scores[opus_key] = score
                st.success(f"✅ {info['title']} を読み込みました")
        
        # データが読み込めない場合はサンプルデータを使用
        if not loaded_scores:
            st.info("オンラインデータが利用できないため、サンプルデータを使用します")
            loaded_scores = self.get_sample_beethoven_data()
        
        return loaded_scores
    
    def extract_musical_features(self, score: m21.stream.Score) -> Dict:
        """楽譜から音楽的特徴を抽出"""
        features = {
            'pitch_data': [],
            'rhythm_data': [],
            'dynamic_data': [],
            'key_areas': [],
            'time_signatures': [],
            'tempo_markings': []
        }
        
        # 各パートを解析
        for part in score.parts:
            # 音高データ
            for note in part.recurse().notes:
                if isinstance(note, m21.note.Note):
                    features['pitch_data'].append({
                        'pitch': note.pitch.midi,
                        'duration': note.quarterLength,
                        'offset': note.offset
                    })
                elif isinstance(note, m21.chord.Chord):
                    features['pitch_data'].append({
                        'pitch': [p.midi for p in note.pitches],
                        'duration': note.quarterLength,
                        'offset': note.offset
                    })
            
            # リズムデータ
            for element in part.recurse():
                if hasattr(element, 'quarterLength') and element.quarterLength > 0:
                    features['rhythm_data'].append(element.quarterLength)
            
            # 強弱記号
            for dynamic in part.recurse().getElementsByClass(m21.dynamics.Dynamic):
                features['dynamic_data'].append({
                    'type': dynamic.value,
                    'offset': dynamic.offset
                })
            
            # 調性
            for key in part.recurse().getElementsByClass(m21.key.Key):
                features['key_areas'].append({
                    'key': str(key),
                    'offset': key.offset
                })
            
            # 拍子
            for ts in part.recurse().getElementsByClass(m21.meter.TimeSignature):
                features['time_signatures'].append({
                    'time_signature': ts.ratioString,
                    'offset': ts.offset
                })
            
            # テンポ
            for tempo in part.recurse().getElementsByClass(m21.tempo.MetronomeMark):
                features['tempo_markings'].append({
                    'bpm': tempo.number,
                    'text': tempo.text if tempo.text else '',
                    'offset': tempo.offset
                })
        
        return features
    
    def prepare_training_data(self, scores: Dict[str, m21.stream.Score]) -> pd.DataFrame:
        """学習用データを準備"""
        all_data = []
        
        for opus_key, score in scores.items():
            features = self.extract_musical_features(score)
            
            # 音符ごとのデータフレームを作成
            for note_data in features['pitch_data']:
                row = {
                    'opus': opus_key,
                    'pitch': note_data['pitch'] if isinstance(note_data['pitch'], int) else note_data['pitch'][0],
                    'duration': note_data['duration'],
                    'offset': note_data['offset']
                }
                
                # 該当する位置の情報を追加
                # 直近の調性
                relevant_keys = [k for k in features['key_areas'] if k['offset'] <= note_data['offset']]
                if relevant_keys:
                    row['key'] = relevant_keys[-1]['key']
                else:
                    row['key'] = 'C major'  # デフォルト
                
                # 直近の拍子
                relevant_ts = [ts for ts in features['time_signatures'] if ts['offset'] <= note_data['offset']]
                if relevant_ts:
                    row['time_signature'] = relevant_ts[-1]['time_signature']
                else:
                    row['time_signature'] = '4/4'  # デフォルト
                
                all_data.append(row)
        
        return pd.DataFrame(all_data)
    
    def get_style_statistics(self, scores: Dict[str, m21.stream.Score]) -> Dict:
        """スタイルの統計情報を取得"""
        stats = {
            'total_works': len(scores),
            'pitch_range': {'min': 127, 'max': 0},
            'common_intervals': {},
            'rhythm_patterns': {},
            'dynamic_markings': {},
            'key_distribution': {},
            'average_tempo': 0
        }
        
        all_pitches = []
        all_intervals = []
        all_rhythms = []
        all_dynamics = []
        all_keys = []
        all_tempos = []
        
        for score in scores.values():
            features = self.extract_musical_features(score)
            
            # 音高範囲
            for note_data in features['pitch_data']:
                if isinstance(note_data['pitch'], int):
                    all_pitches.append(note_data['pitch'])
                else:
                    all_pitches.extend(note_data['pitch'])
            
            # リズムパターン
            all_rhythms.extend(features['rhythm_data'])
            
            # 強弱記号
            all_dynamics.extend([d['type'] for d in features['dynamic_data']])
            
            # 調性
            all_keys.extend([k['key'] for k in features['key_areas']])
            
            # テンポ
            all_tempos.extend([t['bpm'] for t in features['tempo_markings']])
        
        # 統計を計算
        if all_pitches:
            stats['pitch_range']['min'] = min(all_pitches)
            stats['pitch_range']['max'] = max(all_pitches)
        
        # 音程の計算
        for i in range(1, len(all_pitches)):
            interval = all_pitches[i] - all_pitches[i-1]
            if -12 <= interval <= 12:  # オクターブ以内
                all_intervals.append(interval)
        
        # 頻度集計
        from collections import Counter
        
        if all_intervals:
            interval_counts = Counter(all_intervals)
            total_intervals = sum(interval_counts.values())
            stats['common_intervals'] = {
                str(k): v/total_intervals 
                for k, v in interval_counts.most_common(10)
            }
        
        if all_rhythms:
            rhythm_counts = Counter(all_rhythms)
            total_rhythms = sum(rhythm_counts.values())
            stats['rhythm_patterns'] = {
                str(k): v/total_rhythms 
                for k, v in rhythm_counts.most_common(10)
            }
        
        if all_dynamics:
            dynamic_counts = Counter(all_dynamics)
            stats['dynamic_markings'] = dict(dynamic_counts)
        
        if all_keys:
            key_counts = Counter(all_keys)
            stats['key_distribution'] = dict(key_counts)
        
        if all_tempos:
            stats['average_tempo'] = sum(all_tempos) / len(all_tempos)
        
        return stats

class MusicXMLLoader:
    """MusicXMLファイルのローダー（ユーザーアップロード用）"""
    
    @staticmethod
    def load_musicxml(file_path: str) -> Optional[m21.stream.Score]:
        """MusicXMLファイルを読み込む"""
        try:
            score = m21.converter.parse(file_path)
            return score
        except Exception as e:
            st.error(f"MusicXMLの読み込みエラー: {str(e)}")
            return None
    
    @staticmethod
    def validate_score(score: m21.stream.Score) -> Tuple[bool, List[str]]:
        """楽譜の妥当性を検証"""
        issues = []
        
        # パートがあるか
        if len(score.parts) == 0:
            issues.append("パートが見つかりません")
        
        # 音符があるか
        notes = list(score.recurse().notes)
        if len(notes) == 0:
            issues.append("音符が見つかりません")
        
        # 極端に短いか長いか
        total_duration = score.duration.quarterLength
        if total_duration < 4:
            issues.append("楽曲が短すぎます（1小節未満）")
        elif total_duration > 1000:
            issues.append("楽曲が長すぎます（処理に時間がかかる可能性があります）")
        
        is_valid = len(issues) == 0
        return is_valid, issues

# Streamlit用のユーティリティ関数
def display_loaded_scores(scores: Dict[str, m21.stream.Score]):
    """読み込んだ楽譜の情報を表示"""
    if not scores:
        st.warning("楽譜が読み込まれていません")
        return
    
    st.subheader(f"📚 読み込まれた楽譜: {len(scores)}曲")
    
    for opus_key, score in scores.items():
        with st.expander(f"📄 {opus_key}"):
            # 基本情報
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("パート数", len(score.parts))
            
            with col2:
                total_measures = sum(
                    len(part.getElementsByClass('Measure')) 
                    for part in score.parts
                )
                st.metric("小節数", total_measures)
            
            with col3:
                duration = score.duration.quarterLength
                st.metric("長さ（拍）", f"{duration:.1f}")
            
            # 詳細情報
            if opus_key in BeethovenDataLoader().sonata_catalog:
                info = BeethovenDataLoader().sonata_catalog[opus_key]
                st.write(f"**タイトル**: {info['title']}")
                st.write(f"**調性**: {info['key']}")
                st.write(f"**作曲年**: {info['year']}年")
                st.write(f"**時期**: {info['period']}")

def create_download_links(scores: Dict[str, m21.stream.Score]):
    """楽譜のダウンロードリンクを作成"""
    st.subheader("💾 楽譜データのダウンロード")
    
    col1, col2, col3 = st.columns(3)
    
    for i, (opus_key, score) in enumerate(scores.items()):
        col = [col1, col2, col3][i % 3]
        
        with col:
            # MIDIとしてダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mid') as tmp:
                score.write('midi', fp=tmp.name)
                with open(tmp.name, 'rb') as f:
                    midi_data = f.read()
                
                st.download_button(
                    label=f"🎹 {opus_key}.mid",
                    data=midi_data,
                    file_name=f"{opus_key}.mid",
                    mime="audio/midi"
                )
                
                os.unlink(tmp.name)
