"""
BeethovenLab - メインアプリケーション
全てのモジュールを統合した完全版Streamlitアプリ
"""

import streamlit as st
import music21 as m21
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import os
from kern_analyzer import KernAnalyzer
import os
import json

# カスタムモジュールのインポート
try:
    from analysis import (
        BeethovenStyleProfile, 
        analyze_uploaded_file,
        display_analysis_results
    )
    from data_loader import (
        BeethovenDataLoader,
        display_loaded_scores,
        create_download_links
    )
    from generation_engine import (
        BeethovenComposerAdvanced,
        generate_with_advanced_engine,
        display_generation_progress
    )
    from utils import (
        MusicVisualizer,
        FileConverter,
        AnalysisReporter,
        StreamlitHelpers,
        get_beethoven_quote,
        BEETHOVEN_PERIODS,
        MUSICAL_FORMS
    )
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    st.error(f"モジュールの読み込みエラー: {e}")

# ページ設定
st.set_page_config(
    page_title="BeethovenLab - AI作曲システム",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        text-align: center;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-style: italic;
        margin-top: 0;
    }
    .beethoven-quote {
        background-color: #f0f0f0;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        font-style: italic;
    }
    .stButton > button {
        width: 100%;
    }
    .generation-info {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'generated_score' not in st.session_state:
    st.session_state.generated_score = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'loaded_scores' not in st.session_state:
    st.session_state.loaded_scores = {}
if 'style_profile' not in st.session_state:
    st.session_state.style_profile = None
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []
# ベートーヴェンパターンの読み込み
if 'beethoven_patterns' not in st.session_state:
    if os.path.exists("beethoven_patterns.json"):
        # 既存の分析結果を読み込み
        with open("beethoven_patterns.json", "r", encoding="utf-8") as f:
            st.session_state.beethoven_patterns = json.load(f)
    else:
        # 分析を実行
        with st.spinner("ベートーヴェンの楽譜を分析中..."):
            analyzer = KernAnalyzer()
            for kern_dir in ["kern1", "kern2"]:
                if os.path.exists(kern_dir):
                    analyzer.analyze_all_files(kern_dir)
            analyzer.save_analysis("beethoven_patterns.json")
            st.session_state.beethoven_patterns = analyzer.patterns

# ヘッダー
st.markdown('<h1 class="main-header">🎼 BeethovenLab</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">ベートーヴェン中期作品スタイルのAI作曲システム</p>', unsafe_allow_html=True)

# ベートーヴェンの名言
if MODULES_LOADED:
    quote = get_beethoven_quote()
    st.markdown(f'<div class="beethoven-quote">"{quote}"<br>- Ludwig van Beethoven</div>', unsafe_allow_html=True)

# メインタブ
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎵 作曲", 
    "📊 分析", 
    "📚 データ管理", 
    "📈 可視化",
    "ℹ️ 情報"
])

with tab1:
    st.header("🎵 AI作曲")
    
    if not MODULES_LOADED:
        st.error("必要なモジュールが読み込まれていません。")
    else:
        # サイドバーで詳細設定
        with st.sidebar:
            st.header("🎹 作曲設定")
            
            # 基本設定
            st.subheader("基本設定")
            
            form_type = st.selectbox(
                "楽曲形式",
                options=list(MUSICAL_FORMS.keys()),
                format_func=lambda x: MUSICAL_FORMS[x],
                help="生成する楽曲の形式を選択"
            )
            
            total_measures = st.select_slider(
                "楽曲の長さ（小節数）",
                options=[16, 32, 48, 64, 96, 128, 144],
                value=32,
                help="生成する楽曲の総小節数"
            )
            
            # 詳細設定
            with st.expander("🔧 詳細設定", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    tempo_range = st.slider(
                        "テンポ範囲 (BPM)",
                        min_value=60,
                        max_value=180,
                        value=(100, 140),
                        step=10,
                        help="生成される楽曲のテンポ範囲"
                    )
                    
                    key_signature = st.selectbox(
                        "調性",
                        ["C major", "G major", "D major", "A major", 
                         "F major", "B♭ major", "E♭ major",
                         "A minor", "E minor", "D minor", "G minor",
                         "C minor", "F minor"],
                        help="楽曲の調性"
                    )
                
                with col2:
                    complexity_level = st.slider(
                        "複雑度",
                        min_value=1,
                        max_value=5,
                        value=3,
                        help="1: シンプル, 5: 非常に複雑"
                    )
                    
                    dynamic_contrast = st.slider(
                        "強弱対比",
                        min_value=1,
                        max_value=5,
                        value=4,
                        help="ベートーヴェンらしい強弱の対比"
                    )
            
            # スタイル設定
            st.subheader("スタイル設定")
            
            use_custom_profile = st.checkbox(
                "カスタムスタイルプロファイルを使用",
                help="分析タブで作成したプロファイルを使用"
            )
            
            if use_custom_profile and st.session_state.style_profile:
                st.success("✅ カスタムプロファイルを使用")
            elif use_custom_profile:
                st.warning("⚠️ プロファイルが読み込まれていません")

# Kernファイル分析セクション
st.subheader("🔬 楽譜分析")
if st.button("Kernファイルを分析"):
        with st.spinner("分析中... これには数分かかります"):
            analyzer = KernAnalyzer()
            found_files = 0
        
        for kern_dir in ["kern1", "kern2"]:
            if os.path.exists(kern_dir):
                st.write(f"📁 {kern_dir} フォルダを分析中...")
                files = [f for f in os.listdir(kern_dir) if f.endswith('.krn')]
                st.write(f"  - {len(files)} 個のファイルを発見")
                found_files += len(files)
                
                results = analyzer.analyze_all_files(kern_dir)
        
            if found_files > 0:
                analyzer.save_analysis("beethoven_patterns.json")
                st.session_state.beethoven_patterns = analyzer.patterns
                st.success(f"✅ {found_files} 個のファイルの分析が完了しました！")
            
            # 分析結果のプレビュー
            st.write("**分析結果のサンプル:**")
            st.write("最も頻出する音程:")
            patterns = analyzer.get_most_common_patterns('melodic_intervals', 3)
            for interval, count in patterns:
                st.write(f"  - 音程 {interval}: {count}回")
            else:
                st.error("❌ Kernファイルが見つかりません")

            # 生成オプション
            st.subheader("生成オプション")
            
            include_dynamics = st.checkbox("強弱記号を含める", value=True)
            include_articulations = st.checkbox("アーティキュレーションを含める", value=True)
            include_tempo_changes = st.checkbox("テンポ変化を含める", value=True)
            
            st.divider()
            
            # 生成ボタン
            generate_button = st.button(
                "🎼 作曲を開始",
                type="primary",
                use_container_width=True
            )
        
        # メインエリア
        if generate_button:
            start_time = time.time()
            
            # プログレスバーと状態表示
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with progress_placeholder.container():
                progress_bar = st.progress(0)
            
            # 生成プロセス
            status_placeholder.text("🎼 楽曲構造を設計中...")
            progress_bar.progress(0.2)
            time.sleep(0.5)
            
            status_placeholder.text("🎹 主要動機を作成中...")
            progress_bar.progress(0.4)
            time.sleep(0.5)
            
            status_placeholder.text("🎵 和声進行を生成中...")
            progress_bar.progress(0.6)
            time.sleep(0.5)
            
            # 実際の生成
            try:
                # スタイルプロファイルの決定
                style_profile = None
                if use_custom_profile and st.session_state.style_profile:
                    style_profile = st.session_state.style_profile
                
                # 楽曲生成
                score = generate_with_advanced_engine(
                    total_measures=total_measures,
                    form=form_type,
                    style_profile=style_profile
                )
                
                # メタデータの設定
                score.metadata.title = f"BeethovenLab {form_type.title()} in {key_signature}"
                score.metadata.composer = "BeethovenLab AI"
                score.metadata.movementNumber = 1
                
                # セッション状態に保存
                st.session_state.generated_score = score
                
                status_placeholder.text("✨ 最終調整中...")
                progress_bar.progress(0.9)
                time.sleep(0.5)
                
                # 完了
                progress_bar.progress(1.0)
                generation_time = time.time() - start_time
                
                # 生成履歴に追加
                st.session_state.generation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'form': form_type,
                    'measures': total_measures,
                    'key': key_signature,
                    'time': generation_time
                })
                
                status_placeholder.success(f"✅ 作曲が完了しました！（{generation_time:.1f}秒）")
                
            except Exception as e:
                status_placeholder.error(f"生成中にエラーが発生しました: {str(e)}")
                st.stop()
        
        # 生成結果の表示
        if st.session_state.generated_score:
            st.divider()
            
            # 基本情報
            st.subheader("📜 生成された楽曲")
            StreamlitHelpers.display_score_info(st.session_state.generated_score)
            
            # 楽譜の表示（テキスト形式）
            with st.expander("楽譜プレビュー（テキスト形式）"):
                score_text = st.session_state.generated_score.show('text')
                st.text(score_text)
            
            # 再生とダウンロード
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("🎧 再生")
                
                # MIDIデータの生成
                midi_data = FileConverter.score_to_midi(st.session_state.generated_score)
                st.audio(midi_data, format='audio/midi')
                
                # 生成情報
                if st.session_state.generation_history:
                    latest = st.session_state.generation_history[-1]
                    st.markdown(f"""
                    <div class="generation-info">
                    <strong>生成情報:</strong><br>
                    生成時刻: {latest['timestamp']}<br>
                    形式: {MUSICAL_FORMS[latest['form']]}<br>
                    長さ: {latest['measures']}小節<br>
                    生成時間: {latest['time']:.1f}秒
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                # ダウンロードオプション
                StreamlitHelpers.create_download_section(
                    st.session_state.generated_score,
                    base_filename="beethoven_lab_composition"
                )
            
            # フィードバック
            StreamlitHelpers.create_feedback_form()

with tab2:
    st.header("📊 楽曲分析")
    
    if not MODULES_LOADED:
        st.error("必要なモジュールが読み込まれていません。")
    else:
        # データソース選択
        data_source = st.radio(
            "分析するデータを選択",
            ["ファイルをアップロード", "生成済み楽曲", "サンプルデータ"]
        )
        
        score_to_analyze = None
        
        if data_source == "ファイルをアップロード":
            uploaded_file = st.file_uploader(
                "MusicXMLまたはMIDIファイルを選択",
                type=['xml', 'mxl', 'mid', 'midi']
            )
            
            if uploaded_file:
                try:
                    # ファイルの分析
                    st.session_state.analysis_results = analyze_uploaded_file(uploaded_file)
                    st.success("✅ ファイルの分析が完了しました")
                except Exception as e:
                    st.error(f"分析エラー: {str(e)}")
        
        elif data_source == "生成済み楽曲":
            if st.session_state.generated_score:
                score_to_analyze = st.session_state.generated_score
                st.info("生成された楽曲を分析します")
            else:
                st.warning("まだ楽曲が生成されていません")
        
        else:  # サンプルデータ
            if st.button("サンプルデータを読み込む"):
                loader = BeethovenDataLoader()
                sample_scores = loader.get_sample_beethoven_data()
                if sample_scores:
                    score_to_analyze = list(sample_scores.values())[0]
                    st.success("サンプルデータを読み込みました")
        
        # 分析実行
        if score_to_analyze and st.button("🔍 分析を実行"):
            with st.spinner("分析中..."):
                analyzer = BeethovenStyleProfile()
                
                # 各種分析を実行
                st.session_state.analysis_results = {
                    'harmonic': analyzer.harmonic_analyzer.analyze_harmony(score_to_analyze),
                    'melodic': analyzer.melodic_analyzer.analyze_melody(score_to_analyze),
                    'rhythmic': analyzer.rhythmic_analyzer.analyze_rhythm(score_to_analyze),
                    'structural': analyzer.structural_analyzer.analyze_structure(score_to_analyze)
                }
                
                # スタイルプロファイルを作成
                st.session_state.style_profile = analyzer.create_style_profile([score_to_analyze])
                
                st.success("✅ 分析が完了しました")
        
        # 分析結果の表示
        if st.session_state.analysis_results:
            display_analysis_results(st.session_state.analysis_results)
            
            # レポートのダウンロード
            if st.button("📄 分析レポートをダウンロード"):
                report = AnalysisReporter.create_analysis_report(st.session_state.analysis_results)
                st.download_button(
                    label="レポートをダウンロード",
                    data=report,
                    file_name=f"beethoven_lab_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

with tab3:
    st.header("📚 データ管理")
    
    if not MODULES_LOADED:
        st.error("必要なモジュールが読み込まれていません。")
    else:
        # データローダーの初期化
        loader = BeethovenDataLoader()
        
        # データソース選択
        st.subheader("データソース")
        
        data_option = st.selectbox(
            "データの取得方法",
            ["ベートーヴェン中期ソナタ（推奨）", "カスタムファイル", "サンプルデータ"]
        )
        
        if data_option == "ベートーヴェン中期ソナタ（推奨）":
            st.info("ベートーヴェンの中期ピアノソナタを読み込みます")
            
            if st.button("🎹 中期ソナタを読み込む"):
                with st.spinner("データを読み込み中..."):
                    loaded_scores = loader.load_middle_period_sonatas()
                    if loaded_scores:
                        st.session_state.loaded_scores = loaded_scores
                        st.success(f"✅ {len(loaded_scores)}曲を読み込みました")
        
        elif data_option == "カスタムファイル":
            uploaded_files = st.file_uploader(
                "複数のファイルを選択",
                type=['xml', 'mxl', 'mid', 'midi', 'krn'],
                accept_multiple_files=True
            )
            
            if uploaded_files and st.button("ファイルを読み込む"):
                loaded_count = 0
                for file in uploaded_files:
                    try:
                        score = m21.converter.parse(file)
                        st.session_state.loaded_scores[file.name] = score
                        loaded_count += 1
                    except:
                        st.warning(f"⚠️ {file.name} の読み込みに失敗しました")
                
                if loaded_count > 0:
                    st.success(f"✅ {loaded_count}ファイルを読み込みました")
        
        else:  # サンプルデータ
            if st.button("🎼 サンプルデータを使用"):
                sample_scores = loader.get_sample_beethoven_data()
                st.session_state.loaded_scores = sample_scores
                st.success("✅ サンプルデータを読み込みました")
        
        # 読み込まれたデータの表示
        if st.session_state.loaded_scores:
            st.divider()
            display_loaded_scores(st.session_state.loaded_scores)
            
            # データの統計
            if st.button("📊 データ統計を表示"):
                stats = loader.get_style_statistics(st.session_state.loaded_scores)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("総楽曲数", stats['total_works'])
                    st.metric(
                        "音域",
                        f"{m21.pitch.Pitch(stats['pitch_range']['min']).nameWithOctave} - "
                        f"{m21.pitch.Pitch(stats['pitch_range']['max']).nameWithOctave}"
                    )
                
                with col2:
                    if stats['average_tempo'] > 0:
                        st.metric("平均テンポ", f"{stats['average_tempo']:.0f} BPM")
                    
                    if stats['key_distribution']:
                        most_common_key = max(stats['key_distribution'], 
                                             key=stats['key_distribution'].get)
                        st.metric("最頻出調性", most_common_key)
            
            # ダウンロードリンク
            create_download_links(st.session_state.loaded_scores)

with tab4:
    st.header("📈 可視化")
    
    if not MODULES_LOADED:
        st.error("必要なモジュールが読み込まれていません。")
    else:
        # 可視化対象の選択
        viz_target = st.selectbox(
            "可視化する楽曲",
            ["生成された楽曲", "読み込まれたデータ"]
        )
        
        score_to_visualize = None
        
        if viz_target == "生成された楽曲" and st.session_state.generated_score:
            score_to_visualize = st.session_state.generated_score
        elif viz_target == "読み込まれたデータ" and st.session_state.loaded_scores:
            selected_score = st.selectbox(
                "楽曲を選択",
                list(st.session_state.loaded_scores.keys())
            )
            score_to_visualize = st.session_state.loaded_scores[selected_score]
        
        if score_to_visualize:
            # 可視化タイプの選択
            viz_types = st.multiselect(
                "表示する可視化",
                ["ピアノロール", "和声進行", "強弱曲線", "構造図"],
                default=["ピアノロール"]
            )
            
            visualizer = MusicVisualizer()
            
            # 各可視化を表示
            for viz_type in viz_types:
                st.subheader(viz_type)
                
                if viz_type == "ピアノロール":
                    fig = visualizer.create_piano_roll(score_to_visualize)
                    st.pyplot(fig)
                
                elif viz_type == "和声進行":
                    # 簡易的な和声進行の抽出
                    harmony_data = ['I', 'IV', 'V', 'I'] * 8  # サンプルデータ
                    fig = visualizer.create_harmonic_analysis_chart(harmony_data)
                    st.pyplot(fig)
                
                elif viz_type == "強弱曲線":
                    fig = visualizer.create_dynamic_curve(score_to_visualize)
                    st.pyplot(fig)
                
                elif viz_type == "構造図":
                    # 構造プランのサンプル
                    structure_plan = [
                        {'name': 'Introduction', 'measures': 8, 'parent_section': 'introduction'},
                        {'name': 'First Theme', 'measures': 16, 'parent_section': 'exposition'},
                        {'name': 'Second Theme', 'measures': 16, 'parent_section': 'exposition'},
                        {'name': 'Development', 'measures': 32, 'parent_section': 'development'},
                        {'name': 'Recapitulation', 'measures': 24, 'parent_section': 'recapitulation'},
                        {'name': 'Coda', 'measures': 8, 'parent_section': 'coda'}
                    ]
                    fig = visualizer.create_structure_diagram(structure_plan)
                    st.pyplot(fig)
        else:
            st.info("可視化する楽曲を選択してください")

with tab5:
    st.header("ℹ️ BeethovenLabについて")
    
    st.markdown("""
    ## 🎼 概要
    
    BeethovenLabは、ルートヴィヒ・ヴァン・ベートーヴェンの中期作品（1803-1814）の
    スタイルを学習し、そのスタイルで新しいピアノ曲を生成するAIシステムです。
    
    ### 🎯 主な機能
    
    1. **AI作曲**: ベートーヴェン風の楽曲を自動生成
    2. **楽曲分析**: アップロードされた楽曲の詳細分析
    3. **データ管理**: ベートーヴェンの楽曲データの管理
    4. **可視化**: 楽曲構造の視覚的表現
    
    ### 🔬 技術的特徴
    
    - **マルコフ連鎖**: 音高とリズムの生成
    - **階層的生成**: 大規模構造から細部への生成
    - **動機展開**: ベートーヴェン的な主題労作
    - **構造モデル**: ソナタ形式などの楽曲形式
    
    ### 📚 ベートーヴェン中期の特徴
    
    - **英雄的様式**: 力強く劇的な表現
    - **動機の徹底的展開**: 小さな音型から全体を構築
    - **突然の強弱変化**: ドラマティックな対比
    - **拡大された形式**: より長く複雑な構造
    
    ### 🎹 代表的な中期作品
    
    - ピアノソナタ第21番「ワルトシュタイン」Op.53
    - ピアノソナタ第23番「熱情」Op.57
    - ピアノソナタ第26番「告別」Op.81a
    - 交響曲第3番「英雄」Op.55
    - 交響曲第5番「運命」Op.67
    
    ### 👨‍💻 開発情報
    
    - **使用技術**: Python, Streamlit, music21
    - **アルゴリズム**: マルコフ連鎖 + 構造的生成
    - **データソース**: Kern Scores Dataset
    
    ### 📞 お問い合わせ
    
    ご質問やフィードバックは、GitHubリポジトリのIssuesまでお願いします。
    
    ---
    
    <div style='text-align: center; margin-top: 50px;'>
        <p>Made with ❤️ by BeethovenLab Team</p>
        <p>Inspired by the genius of Ludwig van Beethoven (1770-1827)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 統計情報
    if st.session_state.generation_history:
        st.divider()
        st.subheader("📊 使用統計")
        
        history_df = pd.DataFrame(st.session_state.generation_history)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総生成数", len(history_df))
        
        with col2:
            avg_time = history_df['time'].mean()
            st.metric("平均生成時間", f"{avg_time:.1f}秒")
        
        with col3:
            most_used = history_df['form'].value_counts().index[0]
            st.metric("最頻使用形式", MUSICAL_FORMS[most_used])

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>🎼 BeethovenLab v1.0 - AI-Powered Beethoven Style Composition System</p>
</div>
""", unsafe_allow_html=True)
