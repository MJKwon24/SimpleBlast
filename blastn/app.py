from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
import subprocess
import os
import csv

# Flask 브라우저 앱 설정
app = Flask(__name__, template_folder="templates")

# 디렉토리 설정
UPLOAD_FOLDER = "uploads"
DB_FOLDER = "blast_dbs"
RESULT_FOLDER = "results"

# 필요한 디렉토리 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DB_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # 메인 페이지 렌더링
    return render_template('index.html')

@app.route('/blast', methods=['POST'])
def run_blast():
    try:
        # 업로드된 파일 처리
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or uploaded_files[0].filename == '':
            return "파일을 하나 이상 업로드해주세요.", 400

        query_sequence = request.form.get('sequence')
        if not query_sequence:
            return "쿼리 서열을 입력해주세요.", 400

        # 별도된 FASTA 파일 경로
        merged_fasta_path = os.path.join(UPLOAD_FOLDER, "merged.fasta")

        # 여러 파일 별도
        with open(merged_fasta_path, "w") as merged_fasta:
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.read().decode('utf-8')
                merged_fasta.write(file_content + "\n")

        # 데이터베이스 이름 설정
        db_name = os.path.join(DB_FOLDER, "merged_db")

        # makeblastdb 명령어 실행
        makeblastdb_command = f"makeblastdb -in {merged_fasta_path} -dbtype nucl -out {db_name}"
        subprocess.run(makeblastdb_command, shell=True, check=True)

        # 쿼리 서열을 임시 파일로 저장
        query_file_path = os.path.join(UPLOAD_FOLDER, "query_sequence.fasta")
        with open(query_file_path, "w") as f:
            f.write(f">query\n{query_sequence}\n")

        # BLAST 결과 파일 설정
        raw_output_file = os.path.join(RESULT_FOLDER, "raw_result.csv")
        final_output_file = os.path.join(RESULT_FOLDER, "result.csv")

        # blastn 명령어 실행
        blast_command = (
            f"blastn -query {query_file_path} -db {db_name} -out {raw_output_file} "
            f"-outfmt '10 sseqid pident length mismatch qstart qend sstart send evalue bitscore qlen slen qseq sseq' "
            f"-max_target_seqs 5 -max_hsps 5 -num_threads 32 -word_size 11 -evalue 10"
        )
        subprocess.run(blast_command, shell=True, check=True)

        # CSV 파일에 헤더 추가
        header = "sseqid,pident,length,mismatch,qstart,qend,sstart,send,evalue,bitscore,qlen,slen,qseq,sseq\n"
        with open(final_output_file, "w") as final_f:
            final_f.write(header)
            with open(raw_output_file, "r") as raw_f:
                final_f.writelines(raw_f.readlines())

        # 성공 시 결과 페이지로 리디렉션
        return redirect(url_for('view_results', page=1))

    except subprocess.CalledProcessError as e:
        return f"BLAST 실행 오류: {e.output.decode('utf-8')}", 500
    except Exception as e:
        return f"오류 발생: {str(e)}", 500

@app.route('/results/<int:page>')
def view_results(page):
    try:
        # 결과 파일 경로
        final_output_file = os.path.join(RESULT_FOLDER, "result.csv")

        # CSV 파일 읽기
        with open(final_output_file, "r") as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)  # 헤더 추적
            rows = list(csv_reader)    # 데이터 추적

        # 페이지네이션 설정
        items_per_page = 20
        total_items = len(rows)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page

        # 현재 페이지의 데이터 슬라이싱
        page_rows = rows[start_index:end_index]

        # 헤더 설명 정의
        header_tooltips = {
            "qseqid": "쿼리 서열 ID",
            "sseqid": "대상 서열 ID",
            "pident": "서열 간 일치율 (%)",
            "length": "매치된 서열의 길이",
            "mismatch": "불일치 염기 또는 아미노산의 수",
            "gapopen": "값 오픈 횟수",
            "qstart": "쿼리 서열의 매치 시작 위치",
            "qend": "쿼리 서열의 매치 종료 위치",
            "sstart": "대상 서열의 매치 시작 위치",
            "send": "대상 서열의 매치 종료 위치",
            "evalue": "매치의 통계적 유의성 (E-value)",
            "bitscore": "매치의 통계적 점수",
            "qlen": "쿼리 서열의 전체 길이",
            "slen": "대상 서열의 전체 길이",
            "qseq": "쿼리 서열의 매치된 부분",
            "sseq": "대상 서열의 매치된 부분"
        }

        # HTML 페이지 렌더링
        return render_template(
            'result.html',
            headers=headers,
            rows=page_rows,
            header_tooltips=header_tooltips,
            current_page=page,
            total_pages=total_pages,
            download_path='/download'
        )
    except Exception as e:
        return f"오류 발생: {str(e)}"

@app.route('/download')
def download_file():
    # CSV 파일을 다운로드하도록 설정
    final_output_file = os.path.join(RESULT_FOLDER, "result.csv")
    return send_file(final_output_file, as_attachment=True, download_name="blast_result.csv")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
