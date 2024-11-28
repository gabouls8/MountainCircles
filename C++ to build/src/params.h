#ifndef PARAMS_H
#define PARAMS_H

#include <cstddef>
#include <string>
#include <stdexcept>
#include <iostream>
#include "cell.h"
using namespace std;

struct Params {
    size_t global_ncols,global_nrows;
    float homex, homey, finesse, distSol, securite, 
        nodataltitude,cellsize_m,cellsize_over_finesse, 
        xllcorner, yllcorner;
    string output_path, topology;

    Params(int argc, char* argv[]) {
        if (argc < 9) {
            throw runtime_error("Not enough arguments provided. Expected format: ./compute homex homey finesse distSol securite nodataltitude output_path topology");
        }

        // Convert arguments to appropriate types
        homex = stof(argv[1]);
        homey = stof(argv[2]);
        finesse = stoi(argv[3]);
        distSol = stoi(argv[4]);
        securite = stoi(argv[5]);
        nodataltitude = stoi(argv[6]);
        output_path = argv[7];
        topology = argv[8];
    }
};

#endif // PARAMS_H