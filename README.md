# DZip
## improved general-purpose lossless compression based on novel neural network modeling
#### Arxiv: https://arxiv.org/abs/1911.03572
## Description
Data Compression using neural networks


## Requirements
0. GPU
1. python3 (<= 3.6.8)
2. numpy
3. sklearn
4. keras 2.2.2
5. tensorflow (gpu) 1.14


### Download and install dependencies
Download:
```bash
git clone https://github.com/mohit1997/DZip.git
```
To set up virtual environment and dependencies (on Linux):
```bash
cd DZip
python3 -m venv tf
source tf/bin/activate
bash install.sh
```

# USAGE
To run a compression experiment: 

### Running DZip Compression algorithm
#### There are two ways of running DeepZip

##### ENCODING-DECODING (uses cpu and slower)
<!-- 1. Go to [encode-decode](./encode-decode)
2. Place the parsed files in the directory files_to_be_compressed.
3. Run the following command -->

```bash 
cd encode-decode
# Compress using Bootstrap Model
bash compress.sh FILE.txt FILE.dzip bs
# Compress using Combined Model
bash compress.sh FILE.txt FILE.dzip com
# Decompress
bash decompress.sh FILE.dzip decom_FILE
# Verify decompression
bash compare.sh FILE.txt decom_FILE
```

##### Geting bits per symbol required (uses GPU for encoding and faster)

Outputs bits per character of the compressed file. (Doesn't actually compress the file)

```bash
cd coding-gpu
bash get_compression_results.sh files_to_be_compressed/FILE.txt
```


## Links to the Datasets
| File | Link |
|------|------|
|webster|http://sun.aei.polsl.pl/~sdeor/index.php?page=silesia|
|mozilla|http://sun.aei.polsl.pl/~sdeor/index.php?page=silesia|
|h. chr20|ftp://hgdownload.cse.ucsc.edu/goldenPath/hg38/chromosomes/chr20.fa.gz|
|h. chr1|ftp://hgdownload.cse.ucsc.edu/goldenPath/hg38/chromosomes/chr1.fa.gz|
|c.e. genome|ftp://ftp.ensembl.org/pub/release-97/fasta/caenorhabditis_elegans/dna/Caenorhabditis_elegans.WBcel235.dna.toplevel.fa.gz|
|ill-quality|http://bix.ucsd.edu/projects/singlecell/nbt_data.html|
|text8|http://www.mattmahoney.net/dc/textdata.html|
|enwiki9|http://www.mattmahoney.net/dc/textdata.html|
|np-bases|https://github.com/nanopore-wgs-consortium/NA12878|
|np-quality|https://github.com/nanopore-wgs-consortium/NA12878|

##
1. Go to [Datasets](./Datasets)
2. For real datasets, run
```bash
bash get_data.sh
```
3. For synthetic datasets, run
```bash
# For generating XOR-10 dataset
python generate_data.py --data_type 0entropy --markovity 10 --file_name files_to_be_compressed/xor10.txt
# For generating HMM-10 dataset
python generate_data.py --data_type HMM --markovity 10 --file_name files_to_be_compressed/hmm10.txt
```
4. This will generate a folder named `files_to_be_compressed`. This folder contains the parsed files which can be used to recreate the results in our paper.



### Examples

To compress a synthetic sequence XOR-10. 

#### NOTE: We have already provided some sample syntheic sequences (XOR-k and HMM-k) for test runs in [coding-gpu/files_to_be_compressed](./coding-gpu/files_to_be_compressed).

#### Compress using DZip
```bash 
# Compress using Bootstrap Model
bash compress.sh files_to_be_compressed/xor10.txt bs
# Compress using Combined Model
bash compress.sh files_to_be_compressed/xor10.txt com
```
#### Decompress using DZip

```bash 
# Decompress using Bootstrap Model
bash decompress.sh xor10.dzip bs
# Decompress using Combined Model
bash decompress.sh xor10.dzip com
```

#### Check if decoding is successful

```bash
bash compare.sh files_to_be_compressed/xor10.txt decom_xor10
```

### Credits
The arithmetic coding is performed using the code available at [Reference-arithmetic-coding](https://github.com/nayuki/Reference-arithmetic-coding). The code is a part of Project Nayuki.

### Additional Comments

The compression/decompression speed is approximately 5hrs/MB due to the limitation of [keras platform](https://keras.io/getting-started/faq/). The proposed compressor uses Neural Networks to model the sequence, hence requires GPUs for training and inference. However, some of the operations are non deterministic inherent to the the underlying platform. Hence, the training and inference is performed through a CPU on a single thread, making our method less practical for usage. In future, we expect to bypass these limitations, and improve the compression/decompression times significantly (10 minutes/MB).