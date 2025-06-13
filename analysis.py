"""
BeethovenLab - 楽曲分析モジュール
ベートーヴェンのピアノソナタから音楽的特徴を抽出し、
作曲アルゴリズムで使用可能な形式に変換する
"""

import music21 as m21
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import json
import streamlit as st

class HarmonicAnalyzer:
    """和声進行の分析"""
    
    def __init__(self):
        self.progression_matrix = defaultdict(lambda: defaultdict(int))
        self.cadence_patterns = []
        self.modulation_points = []
        
    def analyze_harmony(self, score: m21.stream.Score) -> Dict:
        """楽曲から和声進行を分析"""
        results = {
            'progressions': {},
            'cadences': [],
            'modulations': [],
            'chord_frequencies': {},
            'progression_probabilities': {}
        }
        
        # 和声解析
        for part in score.parts:
            measures = part.getElementsByClass('Measure')
            previous_chord = None
            
            for measure in measures:
                # 各拍の和声を分析
                for beat in range(1, 5):  # 4/4拍子を仮定
                    chord_tones = []
                    
                    # その拍の全ての音を収集
                    for element in measure.getElementsByOffset(beat - 1, beat):
                        if isinstance(element, (m21.note.Note, m21.chord.Chord)):
                            if isinstance(element, m21.note.Note):
                                chord_tones.append(element.pitch)
                            else:
                                chord_tones.extend(element.pitches)
                    
                    if chord_tones:
                        # 和音を判定
                        try:
                            chord = m21.chord.Chord(chord_tones)
                            roman = m21.roman.romanNumeralFromChord(chord, m21.key.Key('C'))
                            current_chord = roman.romanNumeral
                            
                            # 進行を記録
                            if previous_chord:
                                self.progression_matrix[previous_chord][current_chord] += 1
                            
                            previous_chord = current_chord
                        except:
                            pass
        
        # 進行確率を計算
        for chord, next_chords in self.progression_matrix.items():
            total = sum(next_chords.values())
            results['progression_probabilities'][chord] = {
                next_chord: count / total 
                for next_chord, count in next_chords.items()
            }
        
        # カデンツパターンを識別
        results['cadences'] = self._identify_cadences()
        
        return results
    
    def _identify_cadences(self) -> List[Dict]:
        """カデンツパターンを識別"""
        cadences = []
        
        # 完全終止 (V-I)
        if 'V' in self.progression_matrix and 'I' in self.progression_matrix['V']:
            cadences.append({
                'type': 'Perfect Authentic',
                'progression': 'V-I',
                'frequency': self.progression_matrix['V']['I']
            })
        
        # 変格終止 (IV-I)
        if 'IV' in self.progression_matrix and 'I' in self.progression_matrix['IV']:
            cadences.append({
                'type': 'Plagal',
                'progression': 'IV-I',
                'frequency': self.progression_matrix['IV']['I']
            })
        
        return cadences

class MelodicAnalyzer:
    """旋律の分析"""
    
    def __init__(self):
        self.interval_frequencies = Counter()
        self.contour_patterns = []
        self.motivic_fragments = []
        
    def analyze_melody(self, score: m21.stream.Score) -> Dict:
        """旋律線を分析"""
        results = {
            'interval_distribution': {},
            'contour_types': {},
            'average_range': 0,
            'motivic_cells': [],
            'phrase_lengths': []
        }
        
        all_melodies = []
        
        # 各パートから旋律を抽出
        for part in score.parts:
            notes = part.flatten().notes.stream()
            if len(notes) > 0:
                melody_line = []
                
                for note in notes:
                    if isinstance(note, m21.note.Note):
                        melody_line.append(note)
                
                if melody_line:
                    all_melodies.append(melody_line)
        
        # 音程分析
        for melody in all_melodies:
            for i in range(len(melody) - 1):
                interval = melody[i+1].pitch.midi - melody[i].pitch.midi
                self.interval_frequencies[interval] += 1
        
        # 音程分布を正規化
        total_intervals = sum(self.interval_frequencies.values())
        if total_intervals > 0:
            results['interval_distribution'] = {
                str(interval): count / total_intervals
                for interval, count in self.interval_frequencies.items()
            }
        
        # 旋律の輪郭分析
        results['contour_types'] = self._analyze_contours(all_melodies)
        
        # 動機的要素の抽出
        results['motivic_cells'] = self._extract_motifs(all_melodies)
        
        # フレーズ長の分析
        results['phrase_lengths'] = self._analyze_phrase_lengths(all_melodies)
        
        return results
    
    def _analyze_contours(self, melodies: List[List[m21.note.Note]]) -> Dict:
        """旋律の輪郭を分析"""
        contours = {
            'ascending': 0,
            'descending': 0,
            'arch': 0,
            'inverted_arch': 0,
            'stationary': 0
        }
        
        for melody in melodies:
            if len(melody) < 3:
                continue
                
            # 開始、中間、終了の音高を比較
            start_pitch = melody[0].pitch.midi
            mid_pitch = melody[len(melody)//2].pitch.midi
            end_pitch = melody[-1].pitch.midi
            
            if end_pitch > start_pitch + 2:
                contours['ascending'] += 1
            elif end_pitch < start_pitch - 2:
                contours['descending'] += 1
            elif mid_pitch > max(start_pitch, end_pitch) + 2:
                contours['arch'] += 1
            elif mid_pitch < min(start_pitch, end_pitch) - 2:
                contours['inverted_arch'] += 1
            else:
                contours['stationary'] += 1
        
        # 正規化
        total = sum(contours.values())
        if total > 0:
            contours = {k: v/total for k, v in contours.items()}
        
        return contours
    
    def _extract_motifs(self, melodies: List[List[m21.note.Note]]) -> List[List[int]]:
        """繰り返される動機を抽出"""
        motif_candidates = defaultdict(int)
        
        # 3-5音の短いパターンを探す
        for melody in melodies:
            for length in range(3, 6):
                for i in range(len(melody) - length + 1):
                    # 音程パターンを抽出
                    pattern = []
                    for j in range(length - 1):
                        interval = melody[i+j+1].pitch.midi - melody[i+j].pitch.midi
                        pattern.append(interval)
                    
                    pattern_tuple = tuple(pattern)
                    motif_candidates[pattern_tuple] += 1
        
        # 頻出パターンを動機として抽出
        motifs = []
        for pattern, count in motif_candidates.items():
            if count >= 3:  # 3回以上出現
                motifs.append(list(pattern))
        
        return sorted(motifs, key=lambda x: motif_candidates[tuple(x)], reverse=True)[:10]
    
    def _analyze_phrase_lengths(self, melodies: List[List[m21.note.Note]]) -> List[int]:
        """フレーズ長を分析"""
        phrase_lengths = []
        
        for melody in melodies:
            current_phrase_length = 0
            
            for i, note in enumerate(melody):
                current_phrase_length += 1
                
                # 休符または大きな跳躍でフレーズ区切り
                if i < len(melody) - 1:
                    # 次の音との間隔をチェック
                    interval = abs(melody[i+1].pitch.midi - note.pitch.midi)
                    
                    if interval > 7 or note.quarterLength >= 2:  # 跳躍または長い音符
                        phrase_lengths.append(current_phrase_length)
                        current_phrase_length = 0
            
            if current_phrase_length > 0:
                phrase_lengths.append(current_phrase_length)
        
        return phrase_lengths

class RhythmicAnalyzer:
    """リズムパターンの分析"""
    
    def __init__(self):
        self.rhythm_patterns = []
        self.syncopation_frequency = 0
        self.dynamic_patterns = []
        
    def analyze_rhythm(self, score: m21.stream.Score) -> Dict:
        """リズムパターンを分析"""
        results = {
            'common_patterns': [],
            'syncopation_rate': 0,
            'tempo_markings': [],
            'time_signatures': [],
            'dynamic_changes': []
        }
        
        pattern_counter = Counter()
        total_measures = 0
        syncopated_measures = 0
        
        # 各パートのリズムを分析
        for part in score.parts:
            measures = part.getElementsByClass('Measure')
            total_measures += len(measures)
            
            for measure in measures:
                # リズムパターンを抽出
                rhythm_pattern = []
                has_syncopation = False
                
                for element in measure.notesAndRests:
                    if isinstance(element, (m21.note.Note, m21.chord.Chord)):
                        rhythm_pattern.append(element.quarterLength)
                        
                        # シンコペーションの検出
                        if element.beat % 1 != 0:  # オフビート
                            has_syncopation = True
                
                if has_syncopation:
                    syncopated_measures += 1
                
                if rhythm_pattern:
                    pattern_tuple = tuple(rhythm_pattern)
                    pattern_counter[pattern_tuple] += 1
        
        # 最も一般的なリズムパターン
        results['common_patterns'] = [
            list(pattern) for pattern, _ in pattern_counter.most_common(10)
        ]
        
        # シンコペーション率
        if total_measures > 0:
            results['syncopation_rate'] = syncopated_measures / total_measures
        
        # テンポ記号を抽出
        for tempo in score.flatten().getElementsByClass(m21.tempo.MetronomeMark):
            results['tempo_markings'].append({
                'bpm': tempo.number,
                'text': tempo.text if tempo.text else ''
            })
        
        # 拍子記号を抽出
        for ts in score.flatten().getElementsByClass(m21.meter.TimeSignature):
            results['time_signatures'].append(ts.ratioString)
        
        # 強弱記号の変化を分析
        results['dynamic_changes'] = self._analyze_dynamics(score)
        
        return results
    
    def _analyze_dynamics(self, score: m21.stream.Score) -> List[Dict]:
        """強弱記号の変化を分析"""
        dynamic_changes = []
        
        for part in score.parts:
            current_dynamic = 'mf'  # デフォルト
            
            for element in part.flatten():
                if isinstance(element, m21.dynamics.Dynamic):
                    if element.value != current_dynamic:
                        dynamic_changes.append({
                            'from': current_dynamic,
                            'to': element.value,
                            'type': 'sudden' if abs(ord(element.value[0]) - ord(current_dynamic[0])) > 2 else 'gradual'
                        })
                        current_dynamic = element.value
        
        return dynamic_changes

class StructuralAnalyzer:
    """楽曲構造の分析"""
    
    def __init__(self):
        self.sections = []
        self.key_areas = []
        self.thematic_materials = []
        
    def analyze_structure(self, score: m21.stream.Score) -> Dict:
        """楽曲の大規模構造を分析"""
        results = {
            'form': '',
            'sections': [],
            'key_plan': [],
            'proportion_ratios': {},
            'thematic_relationships': []
        }
        
        # 楽曲の長さを取得
        total_measures = sum(len(part.getElementsByClass('Measure')) for part in score.parts)
        
        # セクションを推定（簡易版）
        if total_measures > 0:
            # ソナタ形式を仮定
            exposition_end = int(total_measures * 0.3)
            development_end = int(total_measures * 0.7)
            
            results['sections'] = [
                {'name': 'Exposition', 'start': 1, 'end': exposition_end},
                {'name': 'Development', 'start': exposition_end + 1, 'end': development_end},
                {'name': 'Recapitulation', 'start': development_end + 1, 'end': total_measures}
            ]
            
            results['form'] = 'Sonata Form'
            
            # 比率を計算
            results['proportion_ratios'] = {
                'exposition': exposition_end / total_measures,
                'development': (development_end - exposition_end) / total_measures,
                'recapitulation': (total_measures - development_end) / total_measures
            }
        
        # 調性計画を分析
        results['key_plan'] = self._analyze_key_plan(score)
        
        return results
    
    def _analyze_key_plan(self, score: m21.stream.Score) -> List[Dict]:
        """調性の変化を追跡"""
        key_plan = []
        
        # 簡易的な調性分析
        for i, part in enumerate(score.parts):
            if i == 0:  # 最初のパートのみ分析
                measures = part.getElementsByClass('Measure')
                
                for j in range(0, len(measures), 8):  # 8小節ごとにチェック
                    measure_group = measures[j:j+8]
                    
                    # 音の集合から調を推定
                    pitches = []
                    for measure in measure_group:
                        for note in measure.notes:
                            if isinstance(note, m21.note.Note):
                                pitches.append(note.pitch)
                    
                    if pitches:
                        # 最も可能性の高い調を推定
                        try:
                            key = m21.analysis.discrete.analyzeStream(
                                m21.stream.Stream(pitches), 'key'
                            )
                            key_plan.append({
                                'measure': j + 1,
                                'key': str(key),
                                'confidence': key.correlationCoefficient
                            })
                        except:
                            pass
        
        return key_plan

class BeethovenStyleProfile:
    """ベートーヴェンのスタイルプロファイルを管理"""
    
    def __init__(self):
        self.harmonic_analyzer = HarmonicAnalyzer()
        self.melodic_analyzer = MelodicAnalyzer()
        self.rhythmic_analyzer = RhythmicAnalyzer()
        self.structural_analyzer = StructuralAnalyzer()
        
    def create_style_profile(self, scores: List[m21.stream.Score]) -> Dict:
        """複数の楽曲からスタイルプロファイルを作成"""
        profile = {
            'harmonic': {},
            'melodic': {},
            'rhythmic': {},
            'structural': {},
            'general_characteristics': {}
        }
        
        # 各楽曲を分析して結果を集約
        harmonic_results = []
        melodic_results = []
        rhythmic_results = []
        structural_results = []
        
        for score in scores:
            harmonic_results.append(self.harmonic_analyzer.analyze_harmony(score))
            melodic_results.append(self.melodic_analyzer.analyze_melody(score))
            rhythmic_results.append(self.rhythmic_analyzer.analyze_rhythm(score))
            structural_results.append(self.structural_analyzer.analyze_structure(score))
        
        # 結果を統合
        profile['harmonic'] = self._merge_harmonic_results(harmonic_results)
        profile['melodic'] = self._merge_melodic_results(melodic_results)
        profile['rhythmic'] = self._merge_rhythmic_results(rhythmic_results)
        profile['structural'] = self._merge_structural_results(structural_results)
        
        # ベートーヴェン中期の一般的特徴
        profile['general_characteristics'] = {
            'dynamic_contrasts': 'frequent and sudden',
            'motivic_development': 'extensive',
            'harmonic_rhythm': 'varied',
            'phrase_structure': 'often irregular',
            'texture': 'homophonic with contrapuntal elements',
            'emotional_character': 'dramatic and heroic'
        }
        
        return profile
    
    def _merge_harmonic_results(self, results: List[Dict]) -> Dict:
        """和声分析結果を統合"""
        merged = {
            'progression_probabilities': defaultdict(lambda: defaultdict(float)),
            'common_cadences': [],
            'modulation_frequency': 0
        }
        
        # 進行確率を平均化
        for result in results:
            for chord, progressions in result.get('progression_probabilities', {}).items():
                for next_chord, prob in progressions.items():
                    merged['progression_probabilities'][chord][next_chord] += prob
        
        # 正規化
        for chord in merged['progression_probabilities']:
            total = sum(merged['progression_probabilities'][chord].values())
            if total > 0:
                for next_chord in merged['progression_probabilities'][chord]:
                    merged['progression_probabilities'][chord][next_chord] /= len(results)
        
        return dict(merged)
    
    def _merge_melodic_results(self, results: List[Dict]) -> Dict:
        """旋律分析結果を統合"""
        merged = {
            'interval_preferences': defaultdict(float),
            'contour_distribution': defaultdict(float),
            'common_motifs': [],
            'typical_phrase_lengths': []
        }
        
        # 音程分布を平均化
        for result in results:
            for interval, freq in result.get('interval_distribution', {}).items():
                merged['interval_preferences'][interval] += freq / len(results)
        
        # 輪郭タイプを集計
        for result in results:
            for contour_type, freq in result.get('contour_types', {}).items():
                merged['contour_distribution'][contour_type] += freq / len(results)
        
        # 共通モチーフを収集
        all_motifs = []
        for result in results:
            all_motifs.extend(result.get('motivic_cells', []))
        
        # 頻出モチーフを選択
        motif_counter = Counter(tuple(m) for m in all_motifs)
        merged['common_motifs'] = [
            list(motif) for motif, _ in motif_counter.most_common(20)
        ]
        
        return dict(merged)
    
    def _merge_rhythmic_results(self, results: List[Dict]) -> Dict:
        """リズム分析結果を統合"""
        merged = {
            'common_patterns': [],
            'average_syncopation_rate': 0,
            'typical_tempo_range': {'min': 60, 'max': 180},
            'dynamic_change_frequency': 0
        }
        
        # リズムパターンを集計
        all_patterns = []
        for result in results:
            all_patterns.extend(result.get('common_patterns', []))
        
        pattern_counter = Counter(tuple(p) for p in all_patterns)
        merged['common_patterns'] = [
            list(pattern) for pattern, _ in pattern_counter.most_common(20)
        ]
        
        # シンコペーション率を平均
        syncopation_rates = [r.get('syncopation_rate', 0) for r in results]
        if syncopation_rates:
            merged['average_syncopation_rate'] = np.mean(syncopation_rates)
        
        return merged
    
    def _merge_structural_results(self, results: List[Dict]) -> Dict:
        """構造分析結果を統合"""
        merged = {
            'typical_forms': [],
            'section_proportions': defaultdict(list),
            'key_relationships': []
        }
        
        # フォームを集計
        forms = [r.get('form', '') for r in results if r.get('form')]
        form_counter = Counter(forms)
        merged['typical_forms'] = [
            form for form, _ in form_counter.most_common()
        ]
        
        # セクション比率を集計
        for result in results:
            for section, ratio in result.get('proportion_ratios', {}).items():
                merged['section_proportions'][section].append(ratio)
        
        # 平均比率を計算
        for section in merged['section_proportions']:
            ratios = merged['section_proportions'][section]
            if ratios:
                merged['section_proportions'][section] = {
                    'mean': np.mean(ratios),
                    'std': np.std(ratios)
                }
        
        return dict(merged)
    
    def save_profile(self, profile: Dict, filename: str):
        """プロファイルをJSONファイルに保存"""
        # defaultdictを通常のdictに変換
        def convert_defaultdict(d):
            if isinstance(d, defaultdict):
                d = {k: convert_defaultdict(v) for k, v in d.items()}
            elif isinstance(d, dict):
                d = {k: convert_defaultdict(v) for k, v in d.items()}
            return d
        
        profile_serializable = convert_defaultdict(profile)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profile_serializable, f, indent=2, ensure_ascii=False)
    
    def load_profile(self, filename: str) -> Dict:
        """プロファイルをJSONファイルから読み込み"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

# Streamlit用のヘルパー関数
@st.cache_data
def analyze_uploaded_file(uploaded_file) -> Dict:
    """アップロードされたファイルを分析"""
    try:
        # ファイルを一時保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name
        
        # music21で読み込み
        score = m21.converter.parse(tmp_file_path)
        
        # 分析を実行
        analyzer = BeethovenStyleProfile()
        results = {
            'harmonic': analyzer.harmonic_analyzer.analyze_harmony(score),
            'melodic': analyzer.melodic_analyzer.analyze_melody(score),
            'rhythmic': analyzer.rhythmic_analyzer.analyze_rhythm(score),
            'structural': analyzer.structural_analyzer.analyze_structure(score)
        }
        
        # 一時ファイルを削除
        os.unlink(tmp_file_path)
        
        return results
        
    except Exception as e:
        st.error(f"ファイルの分析中にエラーが発生しました: {str(e)}")
        return {}

def display_analysis_results(results: Dict):
    """分析結果をStreamlitで表示"""
    if not results:
        return
    
    # タブで結果を整理
    tabs = st.tabs(["🎵 和声", "🎼 旋律", "🥁 リズム", "🏛️ 構造"])
    
    with tabs[0]:
        st.subheader("和声分析")
        
        if 'harmonic' in results:
            harmonic = results['harmonic']
            
            # 進行確率を表示
            if 'progression_probabilities' in harmonic:
                st.write("**和声進行の確率**")
                prog_df = pd.DataFrame(harmonic['progression_probabilities']).fillna(0)
                st.dataframe(prog_df.style.format("{:.2%}"))
            
            # カデンツ
            if 'cadences' in harmonic:
                st.write("**カデンツパターン**")
                for cadence in harmonic['cadences']:
                    st.write(f"- {cadence['type']}: {cadence['progression']} (頻度: {cadence['frequency']})")
    
    with tabs[1]:
        st.subheader("旋律分析")
        
        if 'melodic' in results:
            melodic = results['melodic']
            
            # 音程分布
            if 'interval_distribution' in melodic:
                st.write("**音程分布**")
                interval_df = pd.DataFrame(
                    list(melodic['interval_distribution'].items()),
                    columns=['音程', '頻度']
                )
                st.bar_chart(interval_df.set_index('音程'))
            
            # 輪郭タイプ
            if 'contour_types' in melodic:
                st.write("**旋律輪郭の分布**")
                contour_df = pd.DataFrame(
                    list(melodic['contour_types'].items()),
                    columns=['輪郭タイプ', '割合']
                )
                st.dataframe(contour_df)
            
            # モチーフ
            if 'motivic_cells' in melodic:
                st.write("**検出されたモチーフ**")
                for i, motif in enumerate(melodic['motivic_cells'][:5]):
                    st.write(f"{i+1}. 音程パターン: {motif}")
    
    with tabs[2]:
        st.subheader("リズム分析")
        
        if 'rhythmic' in results:
            rhythmic = results['rhythmic']
            
            # リズムパターン
            if 'common_patterns' in rhythmic:
                st.write("**頻出リズムパターン**")
                for i, pattern in enumerate(rhythmic['common_patterns'][:5]):
                    st.write(f"{i+1}. {pattern}")
            
            # シンコペーション率
            if 'syncopation_rate' in rhythmic:
                st.metric("シンコペーション率", f"{rhythmic['syncopation_rate']:.1%}")
            
            # 強弱変化
            if 'dynamic_changes' in rhythmic:
                st.write("**強弱変化**")
                for change in rhythmic['dynamic_changes'][:5]:
                    st.write(f"- {change['from']} → {change['to']} ({change['type']})")
    
    with tabs[3]:
        st.subheader("構造分析")
        
        if 'structural' in results:
            structural = results['structural']
            
            # 形式
            if 'form' in structural:
                st.write(f"**推定される形式**: {structural['form']}")
            
            # セクション
            if 'sections' in structural:
                st.write("**セクション構成**")
                section_df = pd.DataFrame(structural['sections'])
                st.dataframe(section_df)
            
            # 比率
            if 'proportion_ratios' in structural:
                st.write("**セクション比率**")
                ratio_df = pd.DataFrame(
                    list(structural['proportion_ratios'].items()),
                    columns=['セクション', '比率']
                )
                st.bar_chart(ratio_df.set_index('セクション'))
