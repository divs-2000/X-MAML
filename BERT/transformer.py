# coding=utf-8

from __future__ import absolute_import, division, print_function

import argparse
import csv
import logging
import os
import random
import sys

import numpy as np
import torch


from .data_processor import XnliProcessor, MnliProcessor

logger = logging.getLogger(__name__)

class InputFeatures(object):
  """A single set of features of data."""

  def __init__(self,
               input_ids,
               input_mask,
               segment_ids,
               label_id,
               is_real_example=True):
    self.input_ids = input_ids
    self.input_mask = input_mask
    self.segment_ids = segment_ids
    self.label_id = label_id
    self.is_real_example = is_real_example

def convert_examples_to_features(examples, label_list, max_seq_length,
                                 tokenizer, output_mode):
    """Loads a data file into a list of `InputBatch`s."""

    label_map = {label: i for i, label in enumerate(label_list)}

    features = []
    for (ex_index, example) in enumerate(examples):
        if ex_index % 10000 == 0:
            logger.info("Writing example %d of %d" % (ex_index, len(examples)))

        tokens_a = tokenizer.tokenize(example.text_a)

        tokens_b = None
        if example.text_b:
            tokens_b = tokenizer.tokenize(example.text_b)
            # Modifies `tokens_a` and `tokens_b` in place so that the total
            # length is less than the specified length.
            # Account for [CLS], [SEP], [SEP] with "- 3"
            _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
        else:
            # Account for [CLS] and [SEP] with "- 2"
            if len(tokens_a) > max_seq_length - 2:
                tokens_a = tokens_a[:(max_seq_length - 2)]

        # The convention in BERT is:
        # (a) For sequence pairs:
        #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
        #  type_ids: 0   0  0    0    0     0       0 0    1  1  1  1   1 1
        # (b) For single sequences:
        #  tokens:   [CLS] the dog is hairy . [SEP]
        #  type_ids: 0   0   0   0  0     0 0
        #
        # Where "type_ids" are used to indicate whether this is the first
        # sequence or the second sequence. The embedding vectors for `type=0` and
        # `type=1` were learned during pre-training and are added to the wordpiece
        # embedding vector (and position vector). This is not *strictly* necessary
        # since the [SEP] token unambiguously separates the sequences, but it makes
        # it easier for the model to learn the concept of sequences.
        #
        # For classification tasks, the first vector (corresponding to [CLS]) is
        # used as as the "sentence vector". Note that this only makes sense because
        # the entire model is fine-tuned.
        tokens = ["[CLS]"] + tokens_a + ["[SEP]"]
        segment_ids = [0] * len(tokens)

        if tokens_b:
            tokens += tokens_b + ["[SEP]"]
            segment_ids += [1] * (len(tokens_b) + 1)

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        input_mask = [1] * len(input_ids)

        # Zero-pad up to the sequence length.
        padding = [0] * (max_seq_length - len(input_ids))
        input_ids += padding
        input_mask += padding
        segment_ids += padding

        assert len(input_ids) == max_seq_length
        assert len(input_mask) == max_seq_length
        assert len(segment_ids) == max_seq_length

        if output_mode == "classification":
            label_id = label_map[example.label]
        elif output_mode == "regression":
            label_id = float(example.label)
        else:
            raise KeyError(output_mode)

        if ex_index < 5:
            logger.info("*** Example ***")
            logger.info("guid: %s" % (example.guid))
            logger.info("tokens: %s" % " ".join(
                [str(x) for x in tokens]))
            logger.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            logger.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
            logger.info(
                "segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
            logger.info("label: %s (id = %d)" % (example.label, label_id))

        features.append(
            InputFeatures(input_ids=input_ids,
                          input_mask=input_mask,
                          segment_ids=segment_ids,
                          label_id=label_id))
    return features

def convert_example_to_feature(example, label_list, max_seq_length,
                                 tokenizer, output_mode):
    """Loads a data file into a list of `InputBatch`s."""

    label_map = {label: i for i, label in enumerate(label_list)}


    tokens_a = tokenizer.tokenize(example.text_a)

    tokens_b = None
    if example.text_b:
        tokens_b = tokenizer.tokenize(example.text_b)
        # Modifies `tokens_a` and `tokens_b` in place so that the total
        # length is less than the specified length.
        # Account for [CLS], [SEP], [SEP] with "- 3"
        _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
    else:
        # Account for [CLS] and [SEP] with "- 2"
        if len(tokens_a) > max_seq_length - 2:
            tokens_a = tokens_a[:(max_seq_length - 2)]

    # The convention in BERT is:
    # (a) For sequence pairs:
    #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
    #  type_ids: 0   0  0    0    0     0       0 0    1  1  1  1   1 1
    # (b) For single sequences:
    #  tokens:   [CLS] the dog is hairy . [SEP]
    #  type_ids: 0   0   0   0  0     0 0
    #
    # Where "type_ids" are used to indicate whether this is the first
    # sequence or the second sequence. The embedding vectors for `type=0` and
    # `type=1` were learned during pre-training and are added to the wordpiece
    # embedding vector (and position vector). This is not *strictly* necessary
    # since the [SEP] token unambiguously separates the sequences, but it makes
    # it easier for the model to learn the concept of sequences.
    #
    # For classification tasks, the first vector (corresponding to [CLS]) is
    # used as as the "sentence vector". Note that this only makes sense because
    # the entire model is fine-tuned.
    tokens = ["[CLS]"] + tokens_a + ["[SEP]"]
    segment_ids = [0] * len(tokens)

    if tokens_b:
        tokens += tokens_b + ["[SEP]"]
        segment_ids += [1] * (len(tokens_b) + 1)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)

    # The mask has 1 for real tokens and 0 for padding tokens. Only real
    # tokens are attended to.
    input_mask = [1] * len(input_ids)

    # Zero-pad up to the sequence length.
    padding = [0] * (max_seq_length - len(input_ids))
    input_ids += padding
    input_mask += padding
    segment_ids += padding

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    label_id = label_map[example.label]

    feature=InputFeatures(input_ids=input_ids,
                      input_mask=input_mask,
                      segment_ids=segment_ids,
                      label_id=label_id)
    return feature


def _truncate_seq_pair(tokens_a, tokens_b, max_length):
    """Truncates a sequence pair in place to the maximum length."""

    # This is a simple heuristic which will always truncate the longer sequence
    # one token at a time. This makes more sense than truncating an equal percent
    # of tokens from each, since if one sequence is very short then each token
    # that's truncated likely contains more information than a longer sequence.
    while True:
        total_length = len(tokens_a) + len(tokens_b)
        if total_length <= max_length:
            break
        if len(tokens_a) > len(tokens_b):
            tokens_a.pop()
        else:
            tokens_b.pop()

class transformer():
    def __init__(self, bert_model, tokenizer, max_seq_length, task, cuda):
        #self.device = torch.device("cuda:{}".format(cuda) if torch.cuda.is_available() else "cpu")
        self.device = torch.device('cpu')
        self.max_seq_length=max_seq_length

        self.output_modes = {
            "mnli": "classification",
            "xnli": "classification",
        }
        processors = {
            "mnli": MnliProcessor,
            "xnli": XnliProcessor,
        }
        task=task.lower()
        self.processor=processors[task]()
        self.label_list=self.processor.get_labels()
        #/Users/farhadadm/.pytorch_pretrained_bert/
        self.bertmodel = bert_model
        self.tokenizer = tokenizer
        self.bertmodel.eval()
        self.bertmodel.to(self.device)



    def transfer(self, example, task):
        train_feature = convert_example_to_feature(
            example, self.label_list, self.max_seq_length, self.tokenizer, self.output_modes[task])

        input_ids = torch.tensor([train_feature.input_ids],dtype=torch.long).to(self.device)
        input_mask = torch.tensor([train_feature.input_mask], dtype=torch.long).to(self.device)
        segment_ids = torch.tensor([train_feature.segment_ids] , dtype=torch.long).to(self.device)
        #label_ids = torch.tensor([train_feature.label_id] , dtype=torch.long).to(device)

        # Predict hidden states features for each layer
        with torch.no_grad():
            encoded_layer, pooled_output = self.bertmodel(input_ids, segment_ids,input_mask, output_all_encoded_layers=False)
        #logger.info("Number of layers %d" % (len(encoded_layers)))

        return encoded_layer, pooled_output , input_mask





    def pre_transfer(self, example, task):
        train_feature = convert_example_to_feature(
            example, self.label_list, self.max_seq_length, self.tokenizer, self.output_modes[task])

        input_ids = torch.tensor(train_feature.input_ids, dtype=torch.long).to(self.device)
        input_mask = torch.tensor(train_feature.input_mask, dtype=torch.long).to(self.device)
        segment_ids = torch.tensor(train_feature.segment_ids, dtype=torch.long).to(self.device)

        return input_ids, input_mask, segment_ids


    def transfer_after_toknize(self, input_ids,input_mask,segment_ids):

        with torch.no_grad():
            encoded_layer, pooled_output = self.bertmodel(input_ids, segment_ids,input_mask, output_all_encoded_layers=False)
        #logger.info("Number of layers %d" % (len(encoded_layers)))

        return encoded_layer, pooled_output


    def transfer_all(self, examples, task):
        train_features = convert_examples_to_features(
            examples, self.label_list, self.max_seq_length, self.tokenizer, self.output_modes[task])

        all_input_ids = torch.tensor([f.input_ids for f in train_features], dtype=torch.long).to(self.device)
        all_input_mask = torch.tensor([f.input_mask for f in train_features], dtype=torch.long).to(self.device)
        all_segment_ids = torch.tensor([f.segment_ids for f in train_features], dtype=torch.long).to(self.device)
        all_label_ids = torch.tensor([f.label_id for f in train_features], dtype=torch.long).to(self.device)
        # Predict hidden states features for each layer
        with torch.no_grad():
            _, all_pooled_output = self.bertmodel(all_input_ids, all_segment_ids,all_input_mask,output_all_encoded_layers=False)
        #logger.info("Number of layers %d" % (len(all_encoder_layers)))
        return all_pooled_output
