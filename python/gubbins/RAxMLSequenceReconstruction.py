# encoding: utf-8
# Wellcome Trust Sanger Institute
# Copyright (C) 2013  Wellcome Trust Sanger Institute
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os
import sys
import tempfile
import dendropy
import subprocess
import shutil
import time
from random import randint
from Bio import AlignIO

class RAxMLSequenceReconstruction(object):
	def __init__(self, input_alignment_filename, input_tree, output_alignment_filename, output_tree, raxml_internal_sequence_reconstruction_command, verbose = False ):
		self.input_alignment_filename = os.path.abspath(input_alignment_filename)
		self.input_tree = os.path.abspath(input_tree)
		self.output_alignment_filename = output_alignment_filename
		self.output_tree = output_tree
		self.raxml_internal_sequence_reconstruction_command = raxml_internal_sequence_reconstruction_command
		self.verbose = verbose
		
		self.working_dir = tempfile.mkdtemp(dir=os.getcwd())
		self.temp_rooted_tree = self.working_dir +'/' +'rooted_tree.newick'
		self.temp_interal_fasta = self.working_dir +'/' +'internal.fasta'
	
	def reconstruct_ancestor_sequences(self):
		self.root_tree(self.input_tree, self.temp_rooted_tree)
		self.run_raxml_ancestor_command()
		self.convert_raw_ancestral_states_to_fasta(self.raw_internal_sequence_filename(), self.temp_interal_fasta)
		self.combine_fastas(self.input_alignment_filename, self.temp_interal_fasta,self.output_alignment_filename)
		
		if os.path.exists(self.raw_internal_rooted_tree_filename()):
			shutil.move(self.raw_internal_rooted_tree_filename(), self.output_tree)
		shutil.rmtree(self.working_dir)
	
	def run_raxml_ancestor_command(self):
		current_directory = os.getcwd()
		if self.verbose > 0:
			print(self.raxml_reconstruction_command())
		try:
			os.chdir(self.working_dir)
			subprocess.check_call(self.raxml_reconstruction_command(), shell=True)
			os.chdir(current_directory)
		except:
			os.chdir(current_directory)
			sys.exit("Something went wrong while creating the ancestor sequences using RAxML")
		if self.verbose > 0:
			print(int(time.time()))
	
	def raw_internal_sequence_filename(self):
		return self.working_dir +'/RAxML_marginalAncestralStates.internal'
	
	def raw_internal_rooted_tree_filename(self):
		return self.working_dir +'/RAxML_nodeLabelledRootedTree.internal'
	
	def raxml_reconstruction_command(self):
		verbose_suffix = ''
		if self.verbose:
			verbose_suffix = '> /dev/null 2>&1'
		
		return " ".join([self.raxml_internal_sequence_reconstruction_command, ' -s', self.input_alignment_filename, '-t', self.temp_rooted_tree, '-n', 'internal' ,verbose_suffix ])
	
	def root_tree(self, input_tree_filename, output_tree):
		tree  = dendropy.Tree.get_from_path(self.input_tree, 'newick', preserve_underscores=True)
		self.split_all_non_bi_nodes(tree.seed_node)
		
		output_tree_string = tree.as_string(
			schema='newick',
			suppress_leaf_taxon_labels=False,
			suppress_leaf_node_labels=True,
			suppress_internal_taxon_labels=False,
			suppress_internal_node_labels=False,
			suppress_rooting=False,
			suppress_edge_lengths=False,
			unquoted_underscores=True,
			preserve_spaces=False,
			store_tree_weights=False,
			suppress_annotations=True,
			annotations_as_nhx=False,
			suppress_item_comments=True,
			node_label_element_separator=' '
			)
		with open(output_tree, 'w+') as output_file:
			output_file.write(output_tree_string.replace('\'', ''))
			output_file.closed
			
			return output_tree
	
	def convert_raw_ancestral_states_to_fasta(self, input_filename, output_filename):
		with open(input_filename, 'r') as infile:
			with open(output_filename, 'w+') as outfile:
				for sequence_line in infile:
					[sequence_name, sequence_bases] = sequence_line.split(' ')
					sequence_bases = sequence_bases.replace('?', 'N')
					outfile.write('>'+sequence_name+'\n')
					outfile.write(sequence_bases)
    
    # Warning - recursion
	def split_all_non_bi_nodes(self, node):
		if node.is_leaf():
			return None
		elif len(node.child_nodes()) > 2:
			self.split_child_nodes(node)
		for child_node in node.child_nodes():
			self.split_all_non_bi_nodes(child_node)
		return None
	
	def split_child_nodes(self,node):
		all_child_nodes = node.child_nodes()
		first_child = all_child_nodes.pop()
		new_child_node = node.new_child(edge_length=0)
		new_child_node.set_child_nodes(all_child_nodes)
		node.set_child_nodes((first_child,new_child_node))
	
	def combine_fastas(self, input_file1, input_file2, output_file ):
		with open(output_file, 'w') as output_handle:
			for input_file in [input_file1, input_file2]:
				with open(input_file, 'r') as input_handle:
					alignments = AlignIO.parse(input_handle, "fasta")
					AlignIO.write(alignments,output_handle, "fasta")
					input_handle.closed
					output_handle.closed
	 
	
	