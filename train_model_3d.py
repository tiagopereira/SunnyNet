import os
import sys
import torch
import numpy as np
from torch.utils.data import DataLoader, SubsetRandomSampler
from networkUtils.modelWrapper import Model
from networkUtils.dataSets import PopulationDataset3d
from networkUtils.trainingFunctions import train

if __name__ == '__main__':

    ## model parameters ##
    params = {
        'model': 'SunnyNet_7x7', # pick one from networkUtilities/atmosphereFunctions
        'optimizer': 'Adam',     # only works with Adam right now, can add others from torch.optim to networkUtils/modelWrapper.py
        'loss_fxn': 'MSELoss',  # pick one from networkUtils/lossFunctions.py or a pyotch loss function class name ex MSELoss
        'learn_rate': 1e-3,
        'channels': 6,
        'features': 400,
        #'loss_w_range': (0,4),
        #'loss_scale': 3,
        'cuda': {'use_cuda': True, 'multi_gpu': False},
        'mode': 'training'
    }

    ## training configuration ##
    config = {
        'data_path': '/path/to/training/data.hdf5',
        'save_folder': '/path/to/folder/',
        'model_save': 'trained_model.pt',
        'early_stopping': 5, # iterations without lower loss before breaking training loop
        'num_epochs': 50,    # training epochs
        'train_size': 53978, # manually calculate from your train / test split
        'batch_size_train': 128,
        'val_size': 9526,    # manually calculate from your train / test split
        'batch_size_val': 128,
        'num_workers': 64,   # CPU threads
        'alpha': 0.2         # to turn off make None, weight in loss calculation between mass conservation and cell by cell error
    }

    if os.path.exists(os.path.join(config['save_folder'], config['model_save'])):
        print(f'YO! Save path already exists! Exiting...')
        sys.exit(1)


    print('Python VERSION:', sys.version)
    print('pyTorch VERSION:', torch.__version__)
    print('CUDA VERSION: ', torch.version.cuda)
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print('GPU name:', torch.cuda.get_device_name())
        print(f'Number of GPUS: {torch.cuda.device_count()}')
    print(f"Using {params['model']} architecture...")

    print('Creating dataset...')
    tr_data = PopulationDataset3d(config['data_path'], train=True)
    params['height_vector'] = tr_data.z
    val_data = PopulationDataset3d(config['data_path'], train=False)

    print('Creating dataloaders...')
    loader_dict = {}

    train_loader = DataLoader(
        tr_data,
        batch_size = config['batch_size_train'],
        pin_memory = True,
        num_workers = config['num_workers']
    )

    val_loader = DataLoader(
        val_data,
        batch_size = config['batch_size_val'],
        pin_memory = True,
        num_workers = config['num_workers']
    )

    loader_dict['train'] = train_loader
    loader_dict['val'] = val_loader

    h_model = Model(params)
    epoch_loss = train(config, h_model, loader_dict)

    ## save epoch losses for plotting ##
    with open(f"{config['save_folder']}{config['model_save'][:-3]}_loss.txt", "w") as f:
        for i in range(len(epoch_loss['train'])):
            f.write(str(epoch_loss['train'][i]) + '   ' + str(epoch_loss['val'][i]) + '\n')
