"""
BeethovenLab - 高度な生成エンジン
マルコフ連鎖、階層的生成、動機展開を組み合わせた
ベートーヴェン風楽曲生成システム
"""

import music21 as m21
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, deque
import random
from dataclasses import dataclass
from enum import Enum
import streamlit as st

class MusicalContext:
    """音楽的文脈を管理するクラス"""
    
    def __init__(self):
        self.current_key = m21.key.Key('C')
        self.current_time_signature = m21.meter.TimeSignature('4/4')
        self.current_tempo = 120
        self.dynamic_level = 'mf'
        self.phrase_position = 0  # フレーズ内の位置
        self.section_type = 'exposition'  # 現在のセクション
        self.recent_pitches = deque(maxlen=8)  # 直近の音高
        self.harmonic_rhythm = 1.0  # 和声リズム（拍単位）
        self.tension_level = 0.5  # 緊張度（0-1）
        
    def update_pitch_history(self, pitch: int):
        """音高履歴を更新"""
        self.recent_pitches.append(pitch)
    
    def get_pitch_tendency(self) -> str:
        """音高の傾向を取得"""
        if len(self.recent_pitches) < 3:
            return 'neutral'
        
        recent = list(self.recent_pitches)[-3:]
        if recent[-1] > recent[0] + 2:
            return 'ascending'
        elif recent[-1] < recent[0] - 2:
            return 'descending'
        else:
            return 'stable'

@dataclass
class MotivicCell:
    """動機的細胞"""
    intervals: List[int]  # 音程列
    rhythm: List[float]   # リズムパターン
    contour: str         # 輪郭（ascending, descending, arch, etc.）
    importance: float    # 重要度（0-1）

class MarkovChainModel:
    """マルコフ連鎖モデル"""
    
    def __init__(self, order: int = 2):
        self.order = order
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.rhythm_transitions = defaultdict(lambda: defaultdict(int))
        
    def train_pitch(self, pitch_sequence: List[int]):
        """音高列から学習"""
        for i in range(len(pitch_sequence) - self.order):
            state = tuple(pitch_sequence[i:i+self.order])
            next_pitch = pitch_sequence[i+self.order]
            self.transitions[state][next_pitch] += 1
    
    def train_rhythm(self, rhythm_sequence: List[float]):
        """リズム列から学習"""
        for i in range(len(rhythm_sequence) - self.order):
            state = tuple(rhythm_sequence[i:i+self.order])
            next_rhythm = rhythm_sequence[i+self.order]
            self.rhythm_transitions[state][next_rhythm] += 1
    
    def generate_next_pitch(self, current_state: Tuple[int, ...], 
                          context: MusicalContext) -> int:
        """次の音高を生成"""
        if current_state not in self.transitions:
            # 未知の状態の場合、文脈に基づいて生成
            return self._generate_contextual_pitch(current_state, context)
        
        candidates = self.transitions[current_state]
        
        # 文脈に基づいて確率を調整
        adjusted_candidates = self._adjust_pitch_probabilities(
            candidates, context
        )
        
        # 重み付きランダム選択
        pitches = list(adjusted_candidates.keys())
        weights = list(adjusted_candidates.values())
        
        if sum(weights) == 0:
            return current_state[-1]  # 最後の音を繰り返す
        
        return np.random.choice(pitches, p=np.array(weights)/sum(weights))
    
    def _generate_contextual_pitch(self, state: Tuple[int, ...], 
                                  context: MusicalContext) -> int:
        """文脈に基づいて音高を生成"""
        last_pitch = state[-1]
        
        # 音階内の音を優先
        scale_pitches = context.current_key.pitches
        scale_midi = [p.midi % 12 for p in scale_pitches]
        
        # 音域を制限
        candidates = []
        for offset in range(-7, 8):
            new_pitch = last_pitch + offset
            if 48 <= new_pitch <= 84:  # C3-C6
                if new_pitch % 12 in scale_midi:
                    candidates.append(new_pitch)
        
        if not candidates:
            return last_pitch
        
        # 傾向に基づいて選択
        tendency = context.get_pitch_tendency()
        if tendency == 'ascending':
            candidates = [p for p in candidates if p >= last_pitch]
        elif tendency == 'descending':
            candidates = [p for p in candidates if p <= last_pitch]
        
        return random.choice(candidates) if candidates else last_pitch
    
    def _adjust_pitch_probabilities(self, candidates: Dict[int, int], 
                                   context: MusicalContext) -> Dict[int, float]:
        """文脈に基づいて確率を調整"""
        adjusted = {}
        
        for pitch, count in candidates.items():
            weight = float(count)
            
            # 音階内の音を優先
            scale_pitches = [p.midi % 12 for p in context.current_key.pitches]
            if pitch % 12 in scale_pitches:
                weight *= 1.5
            
            # 緊張度に基づく調整
            if context.tension_level > 0.7:
                # 高緊張時は跳躍を許容
                if abs(pitch - list(context.recent_pitches)[-1]) > 4:
                    weight *= 1.2
            else:
                # 低緊張時は順次進行を優先
                if abs(pitch - list(context.recent_pitches)[-1]) <= 2:
                    weight *= 1.3
            
            adjusted[pitch] = weight
        
        return adjusted

class HarmonicGenerator:
    """和声生成器"""
    
    def __init__(self, style_profile: Dict):
        self.progression_rules = self._create_progression_rules()
        self.cadence_patterns = self._create_cadence_patterns()
        self.style_profile = style_profile
        
    def _create_progression_rules(self) -> Dict:
        """和声進行規則を作成"""
        return {
            'I': {'V': 0.3, 'IV': 0.25, 'vi': 0.2, 'ii': 0.15, 'iii': 0.1},
            'ii': {'V': 0.6, 'vii°': 0.2, 'IV': 0.2},
            'iii': {'vi': 0.4, 'IV': 0.3, 'I': 0.3},
            'IV': {'V': 0.4, 'I': 0.3, 'ii': 0.2, 'vii°': 0.1},
            'V': {'I': 0.6, 'vi': 0.25, 'IV': 0.15},
            'vi': {'ii': 0.35, 'IV': 0.35, 'V': 0.3},
            'vii°': {'I': 0.7, 'V': 0.3}
        }
    
    def _create_cadence_patterns(self) -> List[List[str]]:
        """カデンツパターンを作成"""
        return [
            ['ii', 'V', 'I'],      # 完全正格終止
            ['IV', 'V', 'I'],      # 標準的な完全終止
            ['ii', 'V', 'vi'],     # 偽終止
            ['IV', 'I'],           # 変格終止
            ['V', 'I'],            # 単純な完全終止
            ['vii°', 'I'],         # 導音終止
            ['IV', 'V', 'vi'],     # 偽終止の変形
        ]
    
    def generate_progression(self, length: int, context: MusicalContext) -> List[str]:
        """和声進行を生成"""
        progression = ['I']  # 主和音から開始
        
        for i in range(1, length):
            current_chord = progression[-1]
            
            # カデンツポイントかチェック
            if self._is_cadence_point(i, length):
                cadence = self._select_cadence(context)
                if len(cadence) <= length - i:
                    progression.extend(cadence[1:])  # 最初のコードは現在のコード
                    i += len(cadence) - 1
                    continue
            
            # 次のコードを選択
            next_chord = self._select_next_chord(current_chord, context)
            progression.append(next_chord)
        
        return progression
    
    def _is_cadence_point(self, position: int, total_length: int) -> bool:
        """カデンツポイントかどうか判定"""
        # 4小節ごと、または終了近く
        return position % 16 == 15 or position >= total_length - 3
    
    def _select_cadence(self, context: MusicalContext) -> List[str]:
        """カデンツを選択"""
        if context.section_type == 'exposition':
            # 提示部では明確な終止
            return random.choice([
                ['ii', 'V', 'I'],
                ['IV', 'V', 'I']
            ])
        elif context.section_type == 'development':
            # 展開部では偽終止も使用
            return random.choice([
                ['ii', 'V', 'vi'],
                ['IV', 'V', 'vi'],
                ['V', 'vi']
            ])
        else:
            # 再現部では強い終止
            return ['ii', 'V', 'I']
    
    def _select_next_chord(self, current: str, context: MusicalContext) -> str:
        """次の和音を選択"""
        if current not in self.progression_rules:
            return 'I'
        
        candidates = self.progression_rules[current]
        
        # 緊張度に基づいて調整
        adjusted_candidates = {}
        for chord, prob in candidates.items():
            if context.tension_level > 0.7 and chord in ['V', 'vii°']:
                prob *= 1.3  # 高緊張時は属和音を優先
            elif context.tension_level < 0.3 and chord in ['I', 'vi']:
                prob *= 1.2  # 低緊張時は安定和音を優先
            
            adjusted_candidates[chord] = prob
        
        # 確率的に選択
        chords = list(adjusted_candidates.keys())
        probs = list(adjusted_candidates.values())
        probs = np.array(probs) / sum(probs)
        
        return np.random.choice(chords, p=probs)
    
    def realize_harmony(self, chord_symbol: str, context: MusicalContext) -> m21.chord.Chord:
        """和音記号を実際の和音に変換"""
        root_map = {
            'I': 0, 'ii': 2, 'iii': 4, 'IV': 5, 'V': 7, 'vi': 9, 'vii°': 11
        }
        
        # ルート音を決定
        root = context.current_key.tonic.midi + root_map.get(chord_symbol, 0)
        
        # 和音の構成音を決定
        if chord_symbol == 'vii°':
            # 減三和音
            pitches = [root, root + 3, root + 6]
        elif chord_symbol.lower() in ['ii', 'iii', 'vi']:
            # 短三和音
            pitches = [root, root + 3, root + 7]
        else:
            # 長三和音
            pitches = [root, root + 4, root + 7]
        
        # 転回形を選択（ベースラインの動きを考慮）
        inversion = random.choice([0, 0, 0, 1, 1, 2])  # 基本形を優先
        
        # 音域調整
        while pitches[0] < 36:  # C2より低い場合
            pitches = [p + 12 for p in pitches]
        while pitches[0] > 48:  # C3より高い場合
            pitches = [p - 12 for p in pitches]
        
        # 転回
        if inversion > 0:
            pitches = pitches[inversion:] + [pitches[i] + 12 for i in range(inversion)]
        
        chord = m21.chord.Chord(pitches)
        chord.quarterLength = context.harmonic_rhythm
        
        return chord

class MotivicDeveloper:
    """動機展開器"""
    
    def __init__(self):
        self.primary_motifs = []
        self.secondary_motifs = []
        self.development_techniques = [
            self.transpose,
            self.invert,
            self.retrograde,
            self.augment,
            self.diminish,
            self.fragment,
            self.sequence
        ]
    
    def create_primary_motif(self) -> MotivicCell:
        """主要動機を作成"""
        # ベートーヴェン的な動機パターン
        patterns = [
            # 運命の動機風
            MotivicCell([0, 0, 0, -4], [0.5, 0.5, 0.5, 1.5], 'descending', 1.0),
            # 歓喜の歌風
            MotivicCell([2, 2, 1, 2, 2, 1, 2], [0.5] * 7, 'arch', 0.9),
            # 月光風
            MotivicCell([0, 0, 0], [0.5, 0.5, 0.5], 'stable', 0.8),
            # 熱情風
            MotivicCell([-1, -2, -2, 7], [0.25, 0.25, 0.25, 0.75], 'mixed', 0.95)
        ]
        
        motif = random.choice(patterns)
        self.primary_motifs.append(motif)
        return motif
    
    def develop_motif(self, motif: MotivicCell, technique: Optional[str] = None) -> MotivicCell:
        """動機を展開"""
        if technique:
            # 特定の技法を使用
            for tech_func in self.development_techniques:
                if tech_func.__name__ == technique:
                    return tech_func(motif)
        
        # ランダムに技法を選択
        technique_func = random.choice(self.development_techniques)
        return technique_func(motif)
    
    def transpose(self, motif: MotivicCell) -> MotivicCell:
        """移調"""
        interval = random.choice([-7, -5, -3, -2, 2, 3, 5, 7])
        new_intervals = motif.intervals.copy()
        return MotivicCell(
            new_intervals, 
            motif.rhythm.copy(), 
            motif.contour, 
            motif.importance * 0.9
        )
    
    def invert(self, motif: MotivicCell) -> MotivicCell:
        """反転"""
        new_intervals = [-i for i in motif.intervals]
        new_contour = {
            'ascending': 'descending',
            'descending': 'ascending',
            'arch': 'inverted_arch',
            'inverted_arch': 'arch',
            'stable': 'stable',
            'mixed': 'mixed'
        }.get(motif.contour, 'mixed')
        
        return MotivicCell(
            new_intervals,
            motif.rhythm.copy(),
            new_contour,
            motif.importance * 0.85
        )
    
    def retrograde(self, motif: MotivicCell) -> MotivicCell:
        """逆行"""
        return MotivicCell(
            list(reversed(motif.intervals)),
            list(reversed(motif.rhythm)),
            'mixed',
            motif.importance * 0.8
        )
    
    def augment(self, motif: MotivicCell) -> MotivicCell:
        """拡大"""
        return MotivicCell(
            motif.intervals.copy(),
            [r * 2 for r in motif.rhythm],
            motif.contour,
            motif.importance * 0.9
        )
    
    def diminish(self, motif: MotivicCell) -> MotivicCell:
        """縮小"""
        return MotivicCell(
            motif.intervals.copy(),
            [r * 0.5 for r in motif.rhythm],
            motif.contour,
            motif.importance * 0.9
        )
    
    def fragment(self, motif: MotivicCell) -> MotivicCell:
        """断片化"""
        if len(motif.intervals) <= 2:
            return motif
        
        # 前半または後半を取る
        if random.random() < 0.5:
            # 前半
            length = len(motif.intervals) // 2
            return MotivicCell(
                motif.intervals[:length],
                motif.rhythm[:length],
                'fragment',
                motif.importance * 0.7
            )
        else:
            # 後半
            length = len(motif.intervals) // 2
            return MotivicCell(
                motif.intervals[length:],
                motif.rhythm[length:],
                'fragment',
                motif.importance * 0.7
            )
    
    def sequence(self, motif: MotivicCell) -> MotivicCell:
        """反復進行（ゼクエンツ）"""
        # 2-3回繰り返し、毎回移調
        repetitions = random.randint(2, 3)
        new_intervals = []
        new_rhythm = []
        
        for i in range(repetitions):
            transposition = i * random.choice([2, -2, 3, -3])
            for interval in motif.intervals:
                new_intervals.append(interval)
            new_rhythm.extend(motif.rhythm)
        
        return MotivicCell(
            new_intervals,
            new_rhythm,
            'sequence',
            motif.importance
        )

class StructureGenerator:
    """楽曲構造生成器"""
    
    def __init__(self):
        self.form_templates = {
            'sonata': self._create_sonata_template(),
            'rondo': self._create_rondo_template(),
            'theme_variations': self._create_variation_template()
        }
    
    def _create_sonata_template(self) -> Dict:
        """ソナタ形式のテンプレート"""
        return {
            'sections': [
                {
                    'name': 'exposition',
                    'subsections': [
                        {'name': 'first_theme', 'key': 'I', 'character': 'energetic'},
                        {'name': 'transition', 'key': 'I->V', 'character': 'modulatory'},
                        {'name': 'second_theme', 'key': 'V', 'character': 'lyrical'},
                        {'name': 'closing', 'key': 'V', 'character': 'conclusive'}
                    ],
                    'proportion': 0.3
                },
                {
                    'name': 'development',
                    'subsections': [
                        {'name': 'fragmentation', 'key': 'various', 'character': 'unstable'},
                        {'name': 'sequence', 'key': 'various', 'character': 'progressive'},
                        {'name': 'climax', 'key': 'various', 'character': 'intense'},
                        {'name': 'retransition', 'key': 'V/I', 'character': 'preparatory'}
                    ],
                    'proportion': 0.4
                },
                {
                    'name': 'recapitulation',
                    'subsections': [
                        {'name': 'first_theme', 'key': 'I', 'character': 'energetic'},
                        {'name': 'transition_alt', 'key': 'I', 'character': 'stable'},
                        {'name': 'second_theme', 'key': 'I', 'character': 'lyrical'},
                        {'name': 'coda', 'key': 'I', 'character': 'final'}
                    ],
                    'proportion': 0.3
                }
            ]
        }
    
    def _create_rondo_template(self) -> Dict:
        """ロンド形式のテンプレート"""
        return {
            'sections': [
                {'name': 'A', 'key': 'I', 'proportion': 0.15},
                {'name': 'B', 'key': 'V', 'proportion': 0.15},
                {'name': 'A', 'key': 'I', 'proportion': 0.1},
                {'name': 'C', 'key': 'vi', 'proportion': 0.2},
                {'name': 'A', 'key': 'I', 'proportion': 0.1},
                {'name': 'B', 'key': 'I', 'proportion': 0.15},
                {'name': 'A_coda', 'key': 'I', 'proportion': 0.15}
            ]
        }
    
    def _create_variation_template(self) -> Dict:
        """変奏曲形式のテンプレート"""
        return {
            'theme': {'length': 16, 'key': 'I'},
            'variations': [
                {'type': 'melodic', 'technique': 'ornamentation'},
                {'type': 'rhythmic', 'technique': 'syncopation'},
                {'type': 'harmonic', 'technique': 'reharmonization'},
                {'type': 'textural', 'technique': 'contrapuntal'},
                {'type': 'character', 'technique': 'minor_mode'},
                {'type': 'virtuosic', 'technique': 'rapid_figuration'}
            ]
        }
    
    def plan_structure(self, total_measures: int, form: str = 'sonata') -> List[Dict]:
        """楽曲構造を計画"""
        if form not in self.form_templates:
            form = 'sonata'
        
        template = self.form_templates[form]
        structure_plan = []
        
        if form == 'sonata':
            for section in template['sections']:
                section_measures = int(total_measures * section['proportion'])
                
                # サブセクションに分配
                subsection_measures = section_measures // len(section['subsections'])
                
                for subsection in section['subsections']:
                    structure_plan.append({
                        'name': f"{section['name']}_{subsection['name']}",
                        'measures': subsection_measures,
                        'key': subsection['key'],
                        'character': subsection['character'],
                        'parent_section': section['name']
                    })
        
        return structure_plan
        class BeethovenComposerAdvanced:
            """高度なベートーヴェン風作曲システム"""
    
    def __init__(self, style_profile: Optional[Dict] = None):
        self.context = MusicalContext()
        self.markov_model = MarkovChainModel(order=2)
        self.harmonic_generator = HarmonicGenerator(style_profile or {})
        self.motivic_developer = MotivicDeveloper()
        self.structure_generator = StructureGenerator()
        
        # 分析されたパターンを読み込み
        self.beethoven_patterns = None
        try:
            import json
            with open("beethoven_patterns.json", "r", encoding="utf-8") as f:
                self.beethoven_patterns = json.load(f)
                print("ベートーヴェンパターンを読み込みました")
        except:
            print("パターンファイルが見つかりません - デフォルトパターンを使用")
        
        # デフォルトのトレーニングデータ
        self._train_default_patterns()
    
    def _train_default_patterns(self):
        """デフォルトパターンで学習"""
    
    # 分析データがある場合はそれを優先的に使用
        if self.beethoven_patterns:
            # 音程パターンを学習
        if 'melodic_intervals' in self.beethoven_patterns:
            # 頻出する音程シーケンスを作成
            for interval_str, count in self.beethoven_patterns['melodic_intervals'].items():
                try:
                    # 3音パターンの場合
                    if interval_str.startswith('(') and interval_str.endswith(')'):
                        intervals = eval(interval_str)  # タプルとして評価
                        if len(intervals) == 2:
                            # 基準音を60（C4）として、パターンを生成
                            pattern = [60, 60 + intervals[0], 60 + intervals[0] + intervals[1]]
                            # 出現回数に応じて複数回学習
                            for _ in range(min(count // 10, 5)):
                                self.markov_model.train_pitch(pattern)
                except:
                    continue
    
    # 既存のデフォルトパターンも追加（フォールバック用）
    patterns = [
        [60, 62, 64, 65, 67, 69, 71, 72],  # 上行音階
        [72, 71, 69, 67, 65, 64, 62, 60],  # 下行音階
        [60, 64, 67, 72, 67, 64, 60],      # アルペジオ
        [60, 60, 60, 56, 57, 57, 57, 53],  # 運命の動機風
        [60, 62, 64, 60, 64, 65, 67],      # 跳躍を含む
    ]
    
    for pattern in patterns:
        self.markov_model.train_pitch(pattern)
    
    # リズムパターン（既存のまま）
    rhythm_patterns = [
        [1, 1, 1, 1],
        [2, 1, 1],
        [1, 0.5, 0.5, 1, 1],
        [0.5, 0.5, 0.5, 0.5, 2],
        [3, 1],
    ]
    
    for pattern in rhythm_patterns:
        self.markov_model.train_rhythm(pattern)
    
    def compose(self, total_measures: int, form: str = 'sonata') -> m21.stream.Score:
        """完全な楽曲を作曲"""
        score = m21.stream.Score()
        score.metadata = m21.metadata.Metadata()
        score.metadata.title = f"BeethovenLab Composition in {form.title()} Form"
        score.metadata.composer = "BeethovenLab AI"
        
        # 構造を計画
        structure = self.structure_generator.plan_structure(total_measures, form)
        
        # 主要動機を作成
        primary_motif = self.motivic_developer.create_primary_motif()
        
        # 右手と左手のパートを作成
        right_hand = m21.stream.Part()
        right_hand.partName = "Piano Right Hand"
        left_hand = m21.stream.Part()
        left_hand.partName = "Piano Left Hand"
        
        # 各セクションを生成
        current_measure = 0
        
        for section_plan in structure:
            self.context.section_type = section_plan['parent_section']
            
            # セクションの音楽を生成
            section_music = self._generate_section(
                section_plan,
                primary_motif,
                current_measure
            )
            
            # パートに追加
            for element in section_music['right']:
                right_hand.append(element)
            for element in section_music['left']:
                left_hand.append(element)
            
            current_measure += section_plan['measures']
        
        # スコアに追加
        score.insert(0, right_hand)
        score.insert(0, left_hand)
        
        # 最終調整
        # self.apply_final_touches(score)
        
        return score
    
    def _generate_section(self, section_plan: Dict, 
                         primary_motif: MotivicCell,
                         start_measure: int) -> Dict:
        """セクションを生成"""
        measures = section_plan['measures']
        character = section_plan['character']
        
        # キャラクターに基づいて文脈を設定
        self._set_context_for_character(character)
        
        # 和声進行を生成
        harmony = self.harmonic_generator.generate_progression(
            measures * 4,  # 1小節4拍として
            self.context
        )
        
        # 右手（メロディー）を生成
        right_measures = []
        
        for m in range(measures):
            measure = m21.stream.Measure(number=start_measure + m + 1)
            
            # 動機を使用するか決定
            if random.random() < 0.7 and character in ['energetic', 'intense']:
                # 動機的展開
                motif_variant = self.motivic_developer.develop_motif(primary_motif)
                melody_notes = self._realize_motif(motif_variant, self.context)
            else:
                # マルコフ連鎖による生成
                melody_notes = self._generate_markov_melody(4)  # 1小節分
            
            for note in melody_notes:
                measure.append(note)
            
            # 強弱記号を追加
            if m % 4 == 0:
                dynamic = self._select_dynamic(character)
                measure.insert(0, dynamic)
            
            right_measures.append(measure)
        
        # 左手（伴奏）を生成
        left_measures = []
        
        for m in range(measures):
            measure = m21.stream.Measure(number=start_measure + m + 1)
            
            # 和声を実現
            chord_index = m * 4  # 各小節の開始位置
            
            # 伴奏パターンを選択
            if character == 'energetic':
                # アルベルティ・バス
                pattern = self._create_alberti_bass(
                    harmony[chord_index:chord_index+4]
                )
            elif character == 'lyrical':
                # 和音の持続
                pattern = self._create_sustained_chords(
                    harmony[chord_index:chord_index+4]
                )
            elif character == 'intense':
                # トレモロ
                pattern = self._create_tremolo(
                    harmony[chord_index:chord_index+4]
                )
            else:
                # 標準的な伴奏
                pattern = self._create_standard_accompaniment(
                    harmony[chord_index:chord_index+4]
                )
            
            for element in pattern:
                measure.append(element)
            
            left_measures.append(measure)
        
        return {
            'right': right_measures,
            'left': left_measures
        }
    
    def _set_context_for_character(self, character: str):
        """キャラクターに基づいて文脈を設定"""
        character_settings = {
            'energetic': {
                'tension_level': 0.7,
                'dynamic_level': 'f',
                'harmonic_rhythm': 1.0
            },
            'lyrical': {
                'tension_level': 0.3,
                'dynamic_level': 'p',
                'harmonic_rhythm': 2.0
            },
            'intense': {
                'tension_level': 0.9,
                'dynamic_level': 'ff',
                'harmonic_rhythm': 0.5
            },
            'modulatory': {
                'tension_level': 0.6,
                'dynamic_level': 'mf',
                'harmonic_rhythm': 1.0
            },
            'conclusive': {
                'tension_level': 0.2,
                'dynamic_level': 'f',
                'harmonic_rhythm': 2.0
            },
            'unstable': {
                'tension_level': 0.8,
                'dynamic_level': 'mf',
                'harmonic_rhythm': 0.5
            }
        }
        
        settings = character_settings.get(character, {
            'tension_level': 0.5,
            'dynamic_level': 'mf',
            'harmonic_rhythm': 1.0
        })
        
        self.context.tension_level = settings['tension_level']
        self.context.dynamic_level = settings['dynamic_level']
        self.context.harmonic_rhythm = settings['harmonic_rhythm']
    
    def _realize_motif(self, motif: MotivicCell, context: MusicalContext) -> List[m21.note.Note]:
        """動機を実際の音符に変換"""
        notes = []
        
        # 開始音高を決定
        if context.recent_pitches:
            start_pitch = list(context.recent_pitches)[-1]
        else:
            start_pitch = 60  # C4
        
        current_pitch = start_pitch
        
        for interval, rhythm in zip(motif.intervals, motif.rhythm):
            current_pitch += interval
            
            # 音域制限
            if current_pitch < 48:
                current_pitch += 12
            elif current_pitch > 84:
                current_pitch -= 12
            
            note = m21.note.Note(current_pitch)
            note.quarterLength = rhythm
            notes.append(note)
            
            context.update_pitch_history(current_pitch)
        
        return notes
    
    def _generate_markov_melody(self, length: int) -> List[m21.note.Note]:
        """マルコフ連鎖でメロディーを生成"""
        notes = []
        
        # 初期状態
        if len(self.context.recent_pitches) >= 2:
            state = tuple(list(self.context.recent_pitches)[-2:])
        else:
            state = (60, 62)  # C4, D4
        
        # リズム状態
        rhythm_state = (1.0, 1.0)
        
        for _ in range(length):
            # 次の音高
            next_pitch = self.markov_model.generate_next_pitch(state, self.context)
            
            # 次のリズム
            if rhythm_state in self.markov_model.rhythm_transitions:
                rhythm_candidates = self.markov_model.rhythm_transitions[rhythm_state]
                if rhythm_candidates:
                    rhythms = list(rhythm_candidates.keys())
                    weights = list(rhythm_candidates.values())
                    next_rhythm = np.random.choice(rhythms, p=np.array(weights)/sum(weights))
                else:
                    next_rhythm = 1.0
            else:
                next_rhythm = random.choice([0.5, 1.0, 1.0, 2.0])
            
            # 音符を作成
            note = m21.note.Note(next_pitch)
            note.quarterLength = next_rhythm
            notes.append(note)
            
            # 状態を更新
            state = (state[1], next_pitch)
            rhythm_state = (rhythm_state[1], next_rhythm)
            self.context.update_pitch_history(next_pitch)
        
        return notes
    
    def _create_alberti_bass(self, chord_symbols: List[str]) -> List[m21.note.Note]:
        """アルベルティ・バスを作成"""
        notes = []
        
        for symbol in chord_symbols:
            chord = self.harmonic_generator.realize_harmony(symbol, self.context)
            pitches = [p.midi for p in chord.pitches]
            
            # 低音、中音、高音、中音のパターン
            pattern = [pitches[0], pitches[1], pitches[2], pitches[1]]
            
            for pitch in pattern:
                note = m21.note.Note(pitch)
                note.quarterLength = 0.25
                notes.append(note)
        
        return notes
    
    def _create_sustained_chords(self, chord_symbols: List[str]) -> List[m21.chord.Chord]:
        """持続和音を作成"""
        chords = []
        
        for i, symbol in enumerate(chord_symbols):
            if i == 0 or symbol != chord_symbols[i-1]:
                # 新しい和音
                chord = self.harmonic_generator.realize_harmony(symbol, self.context)
                chord.quarterLength = 1.0
                chords.append(chord)
            else:
                # 同じ和音を延長
                if chords:
                    chords[-1].quarterLength += 1.0
        
        return chords
    
    def _create_tremolo(self, chord_symbols: List[str]) -> List[m21.note.Note]:
        """トレモロを作成"""
        notes = []
        
        for symbol in chord_symbols:
            chord = self.harmonic_generator.realize_harmony(symbol, self.context)
            pitches = [p.midi for p in chord.pitches]
            
            # 2音間の急速な交替
            for _ in range(8):  # 32分音符
                note = m21.note.Note(pitches[0])
                note.quarterLength = 0.125
                notes.append(note)
                
                note = m21.note.Note(pitches[2])
                note.quarterLength = 0.125
                notes.append(note)
        
        return notes
    
    def _create_standard_accompaniment(self, chord_symbols: List[str]) -> List[m21.chord.Chord]:
        """標準的な伴奏を作成"""
        elements = []
        
        for symbol in chord_symbols:
            chord = self.harmonic_generator.realize_harmony(symbol, self.context)
            
            # バスノートと和音を分離
            bass_pitch = chord.pitches[0]
            upper_pitches = chord.pitches[1:]
            
            # バスノート
            bass = m21.note.Note(bass_pitch)
            bass.quarterLength = 0.5
            elements.append(bass)
            
            # 上声部の和音
            upper_chord = m21.chord.Chord(upper_pitches)
            upper_chord.quarterLength = 0.5
            elements.append(upper_chord)
        
        return elements
    
    def _select_dynamic(self, character: str) -> m21.dynamics.Dynamic:
        """キャラクターに基づいて強弱を選択"""
        dynamic_map = {
            'energetic': ['f', 'mf', 'f', 'ff'],
            'lyrical': ['p', 'mp', 'p', 'pp'],
            'intense': ['ff', 'f', 'ff', 'fff'],
            'modulatory': ['mf', 'mp', 'mf', 'f'],
            'conclusive': ['f', 'mf', 'f', 'ff'],
            'unstable': ['mp', 'mf', 'f', 'mf']
        }
        
        dynamics = dynamic_map.get(character, ['mf'])
        selected = random.choice(dynamics)
        
        return m21.dynamics.Dynamic(selected)
    
    def apply_final_touches(self, score: m21.stream.Score):
        """最終的な調整を適用"""
        # パートが存在するか確認
        if not score.parts or len(score.parts) == 0:
            return
            
        # テンポ記号を追加
        tempo = m21.tempo.MetronomeMark(number=120, text="Allegro con brio")
        if len(score.parts) > 0 and score.parts[0].measure(1):
            score.parts[0].measure(1).insert(0, tempo)
        
        # 最初の拍子記号
        ts = m21.meter.TimeSignature('4/4')
        for part in score.parts:
            if part.measure(1):
                part.measure(1).insert(0, ts)
        
        # 調号を追加（修正版）
        try:
            key_obj = m21.key.Key('C')
            ks = key_obj.keySignature
            if ks:
                for part in score.parts:
                    if part.measure(1):
                        part.measure(1).insert(0, ks)
        except Exception:
            pass
        
        # フェルマータを最後に追加
        for part in score.parts:
            last_element = None
            for element in part.recurse():
                if isinstance(element, (m21.note.Note, m21.chord.Chord)):
                    last_element = element
            
            if last_element:
                try:
                    last_element.expressions.append(m21.expressions.Fermata())
                except:
                    pass
        
        # 終止感を強化
        try:
            if len(score.parts) > 0:
                measures = score.parts[0].getElementsByClass('Measure')
                if measures:
                    last_measure_num = len(measures)
                    for part in score.parts:
                        last_measure = part.measure(last_measure_num)
                        if last_measure:
                            last_measure.insert(0, m21.tempo.MetronomeMark(number=80, text="ritardando"))
        except:
            pass

# Streamlit用のヘルパー関数
@st.cache_data
def generate_with_advanced_engine(total_measures: int, 
                                form: str = 'sonata',
                                style_profile: Optional[Dict] = None) -> m21.stream.Score:
    """高度なエンジンで楽曲を生成（キャッシュ付き）"""
    composer = BeethovenComposerAdvanced(style_profile)
    return composer.compose(total_measures, form)

def display_generation_progress():
    """生成の進捗を表示"""
    progress_stages = [
        ("🎼 楽曲構造を設計中...", 0.1),
        ("🎹 主要動機を作成中...", 0.2),
        ("🎵 和声進行を生成中...", 0.4),
        ("🎶 メロディーを作曲中...", 0.6),
        ("🎸 伴奏パターンを作成中...", 0.8),
        ("✨ 最終調整中...", 0.9),
        ("✅ 完成！", 1.0)
    ]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for stage_text, progress_value in progress_stages:
        status_text.text(stage_text)
        progress_bar.progress(progress_value)
        import time
        time.sleep(0.5)  # 演出のための遅延
    
    return progress_bar, status_text
