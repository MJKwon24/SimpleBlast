# Contig를 길이가 긴 순으로 정렬한 뒤, Samplename_Contig001 과 같은 방식으로 이름 수정

from Bio import SeqIO

# 입력 파일과 출력 파일 이름
input_file = "OGSG3.fna"
output_file = "OGSG3.fasta"
sample_name = "OGSG3"  # 변경할 샘플 이름

# 시퀀스 읽기
sequences = list(SeqIO.parse(input_file, "fasta"))

# 시퀀스를 길이로 정렬 (내림차순)
sorted_sequences = sorted(sequences, key=lambda x: len(x.seq), reverse=True)

# 이름 변경 및 시퀀스 쓰기
with open(output_file, "w") as output_handle:
    for i, seq in enumerate(sorted_sequences, 1):
        seq.id = f"{sample_name}_contig{i:03d}"  # 이름 변경
        seq.description = ""  # 설명 제거
        SeqIO.write(seq, output_handle, "fasta")

print(f"FASTA 파일이 '{output_file}'로 저장되었습니다!")

