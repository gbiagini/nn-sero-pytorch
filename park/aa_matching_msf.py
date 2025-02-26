#!/usr/bin/env python3

# aa_matching.py - Module for amino acid matching functions

import re
import Bio
from Bio import SeqIO
from Bio import AlignIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio.Alphabet import IUPAC
import pandas as pd
import random

# mature protein sequence offsets differ by locus
# get offsets by examining mature protein length in IMGT/HLA alignment tool
# https://www.ebi.ac.uk/cgi-bin/ipd/imgt/hla/align.cgi - Mature protein
hlaProteinOffset = {
    "A" : 24, # 365 versus 341 mature
    "B" : 24,
    "C" : 24,
    "DRA" : 25,
    "DRB1" : 29,
    "DRB3" : 29,
    "DRB4" : 29,
    "DRB5" : 29,
    "DQA1" : 23,
    "DQB1" : 32,
    "DPA1" : 31,
    "DPB1" : 29,
}

def getMatureProteinOffset(locus):
        return hlaProteinOffset.get(locus, "Invalid HLA Locus")


def adjust_offset(loc, ard_start_pos, ard_start_pos_incomplete, ard_end_pos, ard_end_pos_incomplete, prev=0,
                  prev_inc=0):
    start = ard_start_pos
    end = ard_end_pos
    start_inc = ard_start_pos_incomplete
    end_inc = ard_end_pos_incomplete
    count = mature_protein[start:end].count('-')
    count_inc = mature_protein[start_inc:end_inc].count('-')

    check = count - prev
    check_inc = count_inc - prev_inc

    if (check == 0):
        new_end = end + (count - prev)
        new_end_inc = end_inc + (count_inc - prev_inc)
        newlist = [new_end, new_end_inc]
        return newlist
    else:
        new_end = end + (count - prev)
        prev = count
        if (check_inc != 0):
            new_end_inc = end_inc + (count_inc - prev_inc)
            prev_inc = count_inc
            return adjust_offset(loc, start, start_inc, new_end, new_end_inc, prev, prev_inc)
        else:
            new_end_inc = end_inc
            return adjust_offset(loc, start, start_inc, new_end, new_end_inc, prev, prev_inc=0)


def remove_ins(loc_full_alseq):
    # need to remove the inserts from the reference sequence to print into the IMGT/HLA .txt file
    gapframe = pd.DataFrame.from_dict(loc_full_alseq, orient="index")
    droplist = []
    for i, row in gapframe.iterrows():
        if i == refseq[loc]:
            for name, data in gapframe.iteritems():
                if data[i] == '-':
                    droplist.append(name)
                else:
                    continue
        else:
            continue
    ungapframe = gapframe.drop(droplist, axis=1)
    for j, jrow in ungapframe.iterrows():
        jrow = jrow.to_string(header=False, index=False)
        jrow = jrow.replace('\n', '')
        jrow = jrow.replace(' ', '')
        loc_full_alseq[j] = jrow

    return loc_full_alseq


def generate_IMGT(HLA_full_alseq, dbversion):
    outfile = open("./IMGT_HLA_Full_Protein_" + str(dbversion) + ".txt", "w+")
    outfile.write("Allele\tFull_Protein\n")
    for allele_loctype in HLA_full_alseq:
        outfile.write("HLA-" + allele_loctype + "\t" + str(HLA_full_alseq[allele_loctype]) + "\n")
    outfile.close()
    return


# use only ARD positions
ard_start_pos = {
    "A" : 1,
    "B" : 1,
    "C" : 1,
    "DRB1" : 1,
	"DRB3" : 1,
	"DRB4" : 1,
	"DRB5" : 1,	
    "DQA1" : 1,
    "DQB1" : 1,
    "DPA1" : 1,
    "DPB1" : 1,
}
ard_end_pos = {
    "A" : 182,
    "B" : 182,
    "C" : 182,
    "DRB1" : 94,
	"DRB3" : 94,
	"DRB4" : 94,
	"DRB5" : 94,	
    "DQA1" : 94,
    "DQB1" : 94,
    "DPA1" : 94,
    "DPB1" : 94,
}

# lots of incomplete ARD sequences in IMGT/HLA
# this should be handled in reference alignment, not here
ard_start_pos_incomplete = {
    "A" : 2, # A*02:50
    "B" : 2, # B*07:30
    "C" : 2, # C*01:10
    "DRB1" : 7, # DRB1*08:19
	"DRB3" : 2, # TBD
	"DRB4" : 2, # TBD
	"DRB5" : 2, # TBD
    "DQA1" : 6, # DQA1*01:06
    "DQB1" : 6, # DQB1*05:100
    "DPA1" : 11, # DPA1*01:03:02
    "DPB1" : 6, # DPB1*01:01:03
}
ard_end_pos_incomplete = {
    "A" : 182, # A*02:50
    "B" : 182, # B*07:30
    "C" : 182, # C*01:10
    "DRB1" : 92, # DRB1*08:19
	"DRB3" : 2, # TBD
	"DRB4" : 2, # TBD
	"DRB5" : 2, # TBD
    "DQA1" : 87, # DQA1*01:06
    "DQB1" : 94, # DQB1*05:100
    "DPA1" : 84, # DPA1*01:03:02
    "DPB1" : 92, # DPB1*01:01:03
}

# load protein sequence file to get full protein sequences into SeqRecord file
##seq_filename = "IMGT_HLA_Full_Protein_3330.txt"
##seqfile = open(seq_filename, "r")

loci = ['A', 'B', 'C', 'DRB1', 'DRB345', 'DQA1', 'DQB1', 'DPA1', 'DPB1']

refseq = {
    "A" : "A*01:01:01:01",
    "B" : "B*07:02:01:01",
    "C" : "C*01:02:01:01",
    "DRB1" : "DRB1*01:01:01:01",
    "DRB3" : "DRB3*01:01:01:01",
    "DRB4" : "DRB4*01:01:01:01",
    "DRB5" : "DRB5*01:01:01:01",
    "DQA1" : "DQA1*01:01:01:01",
    "DQB1" : "DQB1*05:01:01:01",
    "DPA1" : "DPA1*01:03:01:01",
    "DPB1" : "DPB1*01:01:01:01",
    }

HLA_full_allele = {} # Full four-field allele names
HLA_seq = {} # Two-field
regex = '\w*\*\d*\:\d*'

## TODO: automate retrieval of newer versions of HLA/IMGT DB if not present on the system
quest = input("Specify HLA/IMGT DB version? (y/n) ")
if (quest == "y") or (quest == "Y"):
    dbversion = input("HLA/IMGT DB version? (x.xx.x) ")
    dbversion = dbversion.strip()
    dbversion = dbversion.replace('.','')
else:
    dbversion = "3390"

for locus in loci:
    seq_filename = "./msf/" + locus + "_prot_" + str(dbversion) + ".msf"
    multipleseq = AlignIO.read(seq_filename, format="msf")

    for record in multipleseq:
        #HLA_full_allele.append(record.id)
        #HLAseq.append(re.match(regex, allele).group())
        loc_full_allele = record.id
        loc_two_field_allele = re.match(regex, loc_full_allele).group()
        full_protein = record.seq

        # skip missing sequences in IMGT/HLA file
        if (len(full_protein) <10): # #NAME?
            print ("Missing Sequence:" + loc_full_allele)
            continue

        (loc,full_allele) = loc_full_allele.split("*")
        mature_protein = full_protein[getMatureProteinOffset(loc):]

        ## TODO: There could still be an issue if there are '-' at the end of the ARD (or, worse, past the initial but before the final). Test cases?
        
        if loc_full_allele == refseq[loc]:
            start = ard_start_pos[loc]
            end = ard_end_pos[loc]
            start_inc = ard_start_pos_incomplete[loc]
            end_inc = ard_end_pos_incomplete[loc]
            count = mature_protein[start:end].count('-')
            count_inc = mature_protein[start_inc:end_inc].count('-')

            ard_end_pos[loc] = end + count
            ard_end_pos_incomplete[loc] = end + count 



        #print(mature_protein)

        mrecord = SeqRecord(mature_protein)


        # full allele name
        HLA_full_allele[loc_full_allele] = mrecord

        # don't overwrite two-field alleles with new sequences - more likely to be incomplete
        if (loc_two_field_allele not in HLA_seq):
            HLA_seq[loc_two_field_allele] = mrecord

        # print (HLA_seqrecord_dict[allele])
        
        # TODO - add feature annotation to SeqIO object
        # https://biopython.org/wiki/SeqRecord
        # e.g. - which allele contain Bw4/Bw6 epitopes, bind LILRB1, etc
        # https://www.biostars.org/p/57549/

        # print (HLA_seqrecord_dict[allele].seq)


# get the AA mature protein subsequence of any HLA allele
# Python strings start at zero, but amino acid sequences start at position 1
def getAAsubstring(allele,start_position,end_position):
	return HLA_seq[allele].seq[start_position+1:end_position]

# get the AA at any position of any HLA allele
def getAAposition(allele,position):
	return HLA_seq[allele].seq[position+1]

# get the SFVT epitope name (with underscore)
def getEpitope(allele,position_list):
	sfvt_list = []
	for position in position_list:
		AA = getAAposition(allele,position)
		sfvt_aa = str(position) + AA
		sfvt_list.append(sfvt_aa)

	sfvt = "_".join(sfvt_list)
	return (sfvt)

# given two alleles at same locus and a position - Yes/No if mismatched
def isPositionMismatched(allele1,allele2,position):
	AA_allele1 = getAAposition(allele1,position)
	AA_allele2 = getAAposition(allele2,position)
	if (AA_allele1 != AA_allele2):
		return True
	else:
		return False

# count number of mismatches at position between donor and recip
# getTruth function from runMatchMC
def count_AA_Mismatches(aa1_donor,aa2_donor,aa1_recip,aa2_recip):
	mm_count = 0
	if ((aa1_donor != aa1_recip) & (aa1_donor != aa2_recip)):
		mm_count+=1
	if ((aa2_donor != aa1_recip) & (aa2_donor != aa2_recip)):
		mm_count+=1
	return mm_count

# count number of mismatches between alleles at a given position, adjusting for donor homozygosity
def count_AA_Mismatches_Allele(allele1_donor,allele2_donor,allele1_recip,allele2_recip,position):
	donor_homoz = 0
	if (allele1_donor == allele2_donor):
		donor_homoz = 1
	aa1_donor = getAAposition(allele1_donor,position)
	aa2_donor = getAAposition(allele2_donor,position)
	aa1_recip = getAAposition(allele1_recip,position)
	aa2_recip = getAAposition(allele2_recip,position)

	mm_count = count_AA_Mismatches(aa1_donor,aa2_donor,aa1_recip,aa2_recip)

	if ((mm_count == 2) & (donor_homoz == 1)):
		mm_count = 1

	return mm_count

def count_AA_Mismatches_SFVT(allele1_donor,allele2_donor,allele1_recip,allele2_recip,position_list):
	donor_homoz = 0
	mm_total = 0
	if (allele1_donor == allele2_donor):
		donor_homoz = 1
	
	# increment MM count for all positions in list
	for position in position_list:
		aa1_donor = getAAposition(allele1_donor,position)
		aa2_donor = getAAposition(allele2_donor,position)
		aa1_recip = getAAposition(allele1_recip,position)
		aa2_recip = getAAposition(allele2_recip,position)

		mm_count = count_AA_Mismatches(aa1_donor,aa2_donor,aa1_recip,aa2_recip)

		if ((mm_count == 2) & (donor_homoz == 1)):
			mm_count = 1

		mm_total = mm_total + mm_count

	return mm_total


def AA_MM(aa1_donor,aa2_donor,aa1_recip,aa2_recip):
	mm_count = 0
	if ((aa1_donor != aa1_recip) & (aa1_donor != aa2_recip)):
		mm_count=1
	if ((aa2_donor != aa1_recip) & (aa2_donor != aa2_recip)):
		mm_count=1
	return mm_count


# any there any mismatches between alleles at a given position
def AA_MM_Allele(allele1_donor,allele2_donor,allele1_recip,allele2_recip,position):
	aa1_donor = getAAposition(allele1_donor,position)
	aa2_donor = getAAposition(allele2_donor,position)
	aa1_recip = getAAposition(allele1_recip,position)
	aa2_recip = getAAposition(allele2_recip,position)

	is_mm = AA_MM(aa1_donor,aa2_donor,aa1_recip,aa2_recip)

	return is_mm

# weighted choice from https://scaron.info/blog/python-weighted-choice.html
def weighted_choice(seq, weights):
    assert len(weights) == len(seq)
    assert abs(1. - sum(weights)) < 1e-6

    x = random.random()
    for i, elmt in enumerate(seq):
        if x <= weights[i]:
            return elmt
        x -= weights[i]