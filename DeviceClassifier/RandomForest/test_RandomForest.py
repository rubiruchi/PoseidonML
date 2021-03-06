'''
Evaluates the performance of a model (second argument) on a directory of
labeled data (first argument).  Results are saved to the path specified by the
third argument.
'''
import json
import logging
import os
import sys
import time

import numpy as np
from poseidonml.Model import Model


logging.basicConfig(level=logging.INFO)


def calc_f1(results, logger, ignore_unknown=False):
    results_by_label = {}
    for file, file_results in results.items():
        if file != 'labels':
            indiv_results = file_results['individual']
            true_label = file_results['label']

            if true_label not in results_by_label:
                if true_label == 'Unknown':
                    if ignore_unknown is False:
                        results_by_label[true_label] = {
                            'tp': 0, 'fp': 0, 'fn': 0}
                else:
                    results_by_label[true_label] = {'tp': 0, 'fp': 0, 'fn': 0}

            for _, classification in indiv_results.items():
                class_label = classification[0][0]
                if class_label == 'Unknown' and ignore_unknown is True:
                    class_label = classification[1][0]
                if class_label not in results_by_label:
                    results_by_label[class_label] = {'tp': 0, 'fp': 0, 'fn': 0}
                if true_label != 'Unknown':
                    if class_label == true_label:
                        results_by_label[true_label]['tp'] += 1
                    if class_label != true_label:
                        results_by_label[true_label]['fn'] += 1
                        results_by_label[class_label]['fp'] += 1
                elif ignore_unknown is False:
                    if class_label == true_label:
                        results_by_label[true_label]['tp'] += 1
                    if class_label != true_label:
                        results_by_label[true_label]['fn'] += 1
                        results_by_label[class_label]['fp'] += 1
    f1s = []
    for label in results_by_label:
        tp = results_by_label[label]['tp']
        fp = results_by_label[label]['fp']
        fn = results_by_label[label]['fn']

        try:
            precision = tp/(tp + fp)
            recall = tp/(tp + fn)
        except Exception as e:
            logger.debug(
                'precision and recall being set to 0 because {0}'.format(str(e)))
            precision = 0
            recall = 0

        if precision == 0 or recall == 0:
            f1 = 0
        else:
            f1 = 2/(1/precision + 1/recall)

        if (tp + fn) > 0:
            f1s.append(f1)

        if f1 is not 'NaN':
            if (tp + fn) > 0:
                logger.info('F1 of {} for {}'.format(f1, label))

    logger.info('Mean F1: {}'.format(np.mean(f1s)))


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    try:
        if 'LOG_LEVEL' in os.environ and os.environ['LOG_LEVEL'] != '':
            logger.setLevel(os.environ['LOG_LEVEL'])
    except Exception as e:
        logger.error(
            'Unable to set logging level because: {0} defaulting to INFO.'.format(str(e)))

    if len(sys.argv) < 2:
        data_dir = '/pcaps'
    else:
        data_dir = sys.argv[1]
    # Load model from specified path
    if len(sys.argv) > 2:
        load_path = sys.argv[2]
    else:
        load_path = '/models/RandomForestModel.pkl'
    if len(sys.argv) > 3:
        save_path = sys.argv[3]
    else:
        save_path = 'models/RandomForestModel.pkl'
    model = Model(duration=None, hidden_size=None, model_type='RandomForest')
    logger.info('Loading model from %s', load_path)
    model.load(load_path)

    # Initialize results dictionary
    results = {}
    results['labels'] = model.labels

    # Get the true label assignments
    logger.info('Getting label assignments')
    with open('opts/label_assignments.json') as handle:
        label_assignments = json.load(handle)

    # Walk through testing directory and get all the pcaps
    logger.info('Getting pcaps')
    pcaps = []
    for dirpath, dirnames, filenames in os.walk(data_dir):
        for filename in filenames:
            name, extension = os.path.splitext(filename)
            if extension == '.pcap':
                pcaps.append(os.path.join(dirpath, filename))

    # Evaluate the model on each pcap
    tick = time.clock()
    file_size = 0
    file_num = 0
    time_slices = 0
    logger.info('processing pcaps')
    for pcap in pcaps:
         # Get the true label
        _, pcap_file = os.path.split(pcap)
        pcap_name = pcap_file.split('-')[0]
        if pcap_name in label_assignments:
            true_label = label_assignments[pcap_name]
        else:
            true_label = 'Unknown'
        single_result = {}
        single_result['label'] = true_label
        logger.info('Reading ' + pcap_file + ' as ' + true_label)
        # Get the internal representations
        representations, _, _, p, _ = model.get_representation(
            pcap, mean=False)
        if representations is not None:
            file_size += os.path.getsize(pcap)
            file_num += 1
            length = representations.shape[0]
            time_slices += length
            single_result['aggregate'] = p
            individual_dict = {}
            # Classify each slice
            logger.info('Computing classifications by slice')
            for i in range(length):
                p_r = model.classify_representation(representations[i])
                individual_dict[i] = p_r
            single_result['individual'] = individual_dict
            results[pcap] = single_result
    tock = time.clock()

    # Save results to path specified by third argument
    if len(sys.argv) >= 4:
        with open(save_path, 'w') as output_file:
            json.dump(results, output_file)
    logger.info('-'*80)
    logger.info('Results with unknowns')
    logger.info('-'*80)
    calc_f1(results, logger)
    logger.info('-'*80)
    logger.info('Results forcing decisions')
    logger.info('-'*80)
    calc_f1(results, logger, ignore_unknown=True)
    logger.info('-'*80)
    logger.info('Analysis statistics')
    logger.info('-'*80)
    elapsed_time = tock - tick
    rate = file_size/(pow(10, 6)*elapsed_time)
    logger.info('Evaluated {0} pcaps in {1} seconds'.format(
        file_num, round(elapsed_time, 3)))
    logger.info('Total data: {0} Mb'.format(file_size/pow(10, 6)))
    logger.info('Total capture time: {0} hours'.format(time_slices/4))
    logger.info('Data processing rate: {0} Mb per second'.format(rate))
    logger.info('time per 15 minute capture {0} seconds'.format(
        (elapsed_time)/(time_slices)))
    logger.info('-'*80)
