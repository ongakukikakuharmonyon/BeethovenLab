"""
Kern形式のベートーヴェン楽譜を分析するモジュール
"""
import music21 as m21
from collections import defaultdict, Counter
import os
import json
from typing import Dict, List, Tuple
import numpy as np

class KernAnalyzer:
    """Kern形式の楽譜を分析してパターンを抽出"""
    
    def __init__(self):
        self.patterns = {
            'melodic_intervals': defaultdict(int),
            'harmonic_progressions': defaultdict(int),
            'rhythm_patterns': defaultdict(int),
            'note_durations': defaultdict(int),
            'dynamics': defaultdict(int),
            'key_signatures': defaultdict(int),
            'time_signatures': defaultdict(int),
            'motifs': [],
            'phrase_structures': []
        }
        
    def load_kern_file(self, filepath: str) -> m21.stream.Score:
        """Kern形式ファイルを読み込み"""
        try:
            # music21はkern形式を直接サポート
            score = m21.converter.parse(filepath)
            return score
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    def analyze_melodic_intervals(self, part: m21.stream.Part):
        """メロディーの音程パターンを分析"""
        notes = [n for n in part.flatten().notes if isinstance(n, m21.note.Note)]
        
        for i in range(len(notes) - 1):
            interval = notes[i+1].pitch.midi - notes[i].pitch.midi
            self.patterns['melodic_intervals'][interval] += 1
            
            # 3音のパターンも記録
            if i < len(notes) - 2:
                pattern = (
                    notes[i+1].pitch.midi - notes[i].pitch.midi,
                    notes[i+2].pitch.midi - notes[i+1].pitch.midi
                )
                self.patterns['melodic_intervals'][str(pattern)] += 1
    
    def analyze_harmony(self, score: m21.stream.Score):
        """和声進行を分析"""
        # 簡易的な和声分析
        for measure in score.parts[0].getElementsByClass('Measure'):
            chords_in_measure = []
            
            # 各拍で垂直的に音を収集
            for offset in [0, 1, 2, 3]:  # 4/4拍子を仮定
                notes_at_offset = []
                for part in score.parts:
                    notes = part.flatten().getElementsByOffset(
                        measure.offset + offset,
                        measure.offset + offset + 0.5,
                        includeEndBoundary=False
                    )
                    notes_at_offset.extend([n.pitch for n in notes if hasattr(n, 'pitch')])
                
                if notes_at_offset:
                    # 簡易的なコード判定
                    chord_type = self._identify_chord(notes_at_offset)
                    if chord_type:
                        chords_in_measure.append(chord_type)
            
            # 進行を記録
            for i in range(len(chords_in_measure) - 1):
                progression = f"{chords_in_measure[i]}->{chords_in_measure[i+1]}"
                self.patterns['harmonic_progressions'][progression] += 1
    
    def analyze_rhythm(self, part: m21.stream.Part):
        """リズムパターンを分析"""
        durations = []
        for element in part.flatten().notesAndRests:
            durations.append(element.duration.quarterLength)
            self.patterns['note_durations'][element.duration.quarterLength] += 1
        
        # リズムパターン（4音単位）を記録
        for i in range(0, len(durations) - 3, 2):
            pattern = tuple(durations[i:i+4])
            self.patterns['rhythm_patterns'][str(pattern)] += 1
    
    def extract_motifs(self, part: m21.stream.Part, min_length=4, max_length=8):
        """モチーフを抽出"""
        notes = [n for n in part.flatten().notes if isinstance(n, m21.note.Note)]
        
        for length in range(min_length, min(max_length + 1, len(notes))):
            for i in range(len(notes) - length + 1):
                motif = []
                for j in range(length):
                    motif.append({
                        'pitch': notes[i+j].pitch.nameWithOctave,
                        'duration': notes[i+j].duration.quarterLength
                    })
                
                # 同じモチーフが他の場所にも現れるか確認
                if self._count_motif_occurrences(notes, motif, i) > 1:
                    self.patterns['motifs'].append(motif)
    
    def _identify_chord(self, pitches: List[m21.pitch.Pitch]) -> str:
        """音のリストから和音を識別（簡易版）"""
        if not pitches:
            return None
            
        # ピッチクラスのセットを作成
        pitch_classes = set(p.pitchClass for p in pitches)
        
        # 主要な三和音のパターン
        major_triads = {
            (0, 4, 7): 'C', (1, 5, 8): 'Db', (2, 6, 9): 'D',
            (3, 7, 10): 'Eb', (4, 8, 11): 'E', (5, 9, 0): 'F',
            (6, 10, 1): 'Gb', (7, 11, 2): 'G', (8, 0, 3): 'Ab',
            (9, 1, 4): 'A', (10, 2, 5): 'Bb', (11, 3, 6): 'B'
        }
        
        minor_triads = {
            (0, 3, 7): 'Cm', (1, 4, 8): 'C#m', (2, 5, 9): 'Dm',
            (3, 6, 10): 'Ebm', (4, 7, 11): 'Em', (5, 8, 0): 'Fm',
            (6, 9, 1): 'F#m', (7, 10, 2): 'Gm', (8, 11, 3): 'G#m',
            (9, 0, 4): 'Am', (10, 1, 5): 'Bbm', (11, 2, 6): 'Bm'
        }
        
        # 照合
        for triad, chord_name in {**major_triads, **minor_triads}.items():
            if pitch_classes == set(triad):
                return chord_name
                
        return 'Unknown'
    
    def _count_motif_occurrences(self, notes: List[m21.note.Note], 
                                motif: List[Dict], start_idx: int) -> int:
        """モチーフの出現回数をカウント"""
        count = 0
        motif_length = len(motif)
        
        for i in range(len(notes) - motif_length + 1):
            if i == start_idx:
                continue
                
            match = True
            for j in range(motif_length):
                # 移調を考慮した比較
                if j > 0:
                    original_interval = (
                        m21.note.Note(motif[j]['pitch']).pitch.midi - 
                        m21.note.Note(motif[j-1]['pitch']).pitch.midi
                    )
                    current_interval = (
                        notes[i+j].pitch.midi - notes[i+j-1].pitch.midi
                    )
                    if original_interval != current_interval:
                        match = False
                        break
                        
                # リズムの比較
                if notes[i+j].duration.quarterLength != motif[j]['duration']:
                    match = False
                    break
                    
            if match:
                count += 1
                
        return count
    
    def analyze_all_files(self, directory: str) -> Dict:
        """ディレクトリ内の全kernファイルを分析"""
        results = {
            'total_files': 0,
            'analyzed_files': 0,
            'patterns': self.patterns
        }
        
        for filename in os.listdir(directory):
            if filename.endswith('.krn'):
                results['total_files'] += 1
                filepath = os.path.join(directory, filename)
                
                score = self.load_kern_file(filepath)
                if score:
                    print(f"Analyzing {filename}...")
                    
                    # 各パートを分析
                    for part in score.parts:
                        self.analyze_melodic_intervals(part)
                        self.analyze_rhythm(part)
                        self.extract_motifs(part)
                    
                    # スコア全体の分析
                    self.analyze_harmony(score)
                    
                    # メタデータ
                    if score.metadata.timeSignature:
                        self.patterns['time_signatures'][
                            str(score.metadata.timeSignature)
                        ] += 1
                    
                    results['analyzed_files'] += 1
        
        return results
    
    def get_most_common_patterns(self, pattern_type: str, top_n: int = 10) -> List:
        """最も頻出するパターンを取得"""
        if pattern_type not in self.patterns:
            return []
            
        pattern_dict = self.patterns[pattern_type]
        if isinstance(pattern_dict, dict):
            return Counter(pattern_dict).most_common(top_n)
        else:
            return pattern_dict[:top_n]
    
    def save_analysis(self, filepath: str):
        """分析結果を保存"""
        # defaultdictを通常のdictに変換
        save_data = {}
        for key, value in self.patterns.items():
            if isinstance(value, defaultdict):
                save_data[key] = dict(value)
            else:
                save_data[key] = value
                
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    def load_analysis(self, filepath: str):
        """保存された分析結果を読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for key, value in data.items():
            if isinstance(value, dict):
                self.patterns[key] = defaultdict(int, value)
            else:
                self.patterns[key] = value


# 使用例
if __name__ == "__main__":
    analyzer = KernAnalyzer()
    
    # kernファイルのディレクトリを指定
    kern_directories = ["kern1", "kern2"]  # kern1とkern2の両方
    
    for kern_dir in kern_directories:
        if os.path.exists(kern_dir):
            print(f"\n{kern_dir}を分析中...")
            results = analyzer.analyze_all_files(kern_dir)
    
    # 結果表示
    print(f"\n分析完了!")
    
    print("\n最も頻出する音程:")
    for interval, count in analyzer.get_most_common_patterns('melodic_intervals', 5):
        print(f"  {interval}: {count}回")
    
    print("\n最も頻出する和声進行:")
    for progression, count in analyzer.get_most_common_patterns('harmonic_progressions', 5):
        print(f"  {progression}: {count}回")
    
    # 分析結果を保存
    analyzer.save_analysis("beethoven_patterns.json")
