import numpy as np
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

def MaxMinExtend(data, extension=0.5):
    # Return the min and max of data, but stretched by extension*range
    rMin = min(data)
    rMax = max(data)
    rRange = rMax - rMin
    return (rMin - rRange * extension, rMax + rRange * extension)

def signed_quadratic_features(data, features, include_bias=False):
    result = np.zeros(data.shape)
    for i in range(len(data)):
        to_add = np.zeros(data.shape[1])
        square_indices = [int(j*features - j*(j-1)/2) for j in range(features)]
        to_add[:features] = data[i,:features]
        for j in range(features, data.shape[1]):
            if j-features in square_indices:
                ft = square_indices.index(j-features)
                if data[i,ft] < 0:
                    to_add[j] = -data[i,j]
                else:
                    to_add[j] = data[i,j]
            else:
                to_add[j] = data[i,j]
        result[i,:] = to_add
    return result

class Graphing:
    array = None
    errors = None
    
    def FitData(data):
        Graphing.array = np.asarray(data)

    def FitErrors(vert_errors, hori_errors):
        Graphing.errors = (np.asarray(vert_errors)**2 + np.asarray(hori_errors)**2)**0.5
    
    def DataGraph():
        assert not Graphing.array is None, "Need to fit data points; use Graphing.FitData"
        colors = [(min(max(0, 2 - 4*s/45), 1), \
                   min(max(0, 2 - abs((4*s-90)/45)), 1), \
                   min(max(0, 4*s/45 - 2), 1)) for s in Graphing.array[:,2]]
        plt.scatter(Graphing.array[:,0], Graphing.array[:,1], c=colors, alpha=0.5)
        plt.title("Vertical Angle Regression Data")
        plt.xlabel("Distance")
        plt.ylabel("Elevation")
        plt.show()

    def HorizontalDataGraph():
        #Hori_shots append (horz_angle_between shooter and target, distance to target, target's tangential velocity, aiming_yaw)
        assert not Graphing.array is None, "Need to fit data points; use Graphing.FitData"
        colors = [(min(max(0, 2 - 4*s/45), 1), \
                   min(max(0, 2 - abs((4*s-90)/45)), 1), \
                   min(max(0, 4*s/45 - 2), 1)) for s in Graphing.array[:,3]]
        #graph on tangential velocity vs target's distance
        plt.scatter(Graphing.array[:,2], Graphing.array[:,1], c=colors, alpha=0.5)
        plt.title("Horizontal Angle Regression Data")
        plt.xlabel("Tangential Velocity")
        plt.ylabel("Distance")
        plt.show()

    def PredictionGraph(defaults, title="", xlabel="", ylabel=""):
        assert not Graphing.array is None, "Need to fit data points; use Graphing.FitData"
        assert len(defaults) + 1 == len(Graphing.array[0]), "Default values list must be same shape as samples"
        assert None in defaults, "Need exactly 1 or 2 non-default values in samples"
        #Vert_shots append (distance from target, difference in Y between shooter and target, aiming_pitch)

        # Get indices where no default values provided
        indices = []
        for i in range(len(defaults)):
            if defaults[i] is None:
                indices.append(i)
        assert len(indices) < 3, "Need exactly 1 or 2 non-default values in samples"
        
        poly = PolynomialFeatures(2, include_bias=False).fit(Graphing.array[:,:-1])
        predictor = LinearRegression().fit(signed_quadratic_features(poly.transform(Graphing.array[:,:-1]), len(defaults)), Graphing.array[:,-1])

        # If only 1 data point to graph, use line graph
        if len(indices) == 1:
            xMin, xMax = MaxMinExtend(Graphing.array[:,indices[0]], 0.1)
            xx = np.linspace(xMin, xMax, 100)
            yy = np.zeros(xx.shape)
            for i in range(xx.shape[0]):
                predictData = defaults
                predictData[indices[0]] = xx[i]
                yy[i] = predictor.predict(signed_quadratic_features(poly.transform([predictData]), len(defaults)))[0]
            cs = plt.plot(xx, yy)

        # If 2 data ponits to graph, use topological graph    
        else:
            xMin, xMax = MaxMinExtend(Graphing.array[:,indices[0]], 0.1)
            yMin, yMax = MaxMinExtend(Graphing.array[:,indices[1]], 0.1)
            xSpace = np.linspace(xMin, xMax, 100)
            ySpace = np.linspace(yMin, yMax, 100)
            xx, yy = np.meshgrid(xSpace, ySpace)
            zz = np.zeros(xx.shape)
            for i in range(xx.shape[0]):
                for j in range(xx.shape[1]):
                    predictData = defaults
                    predictData[indices[0]] = xx[i,j]
                    predictData[indices[1]] = yy[i,j]
                    zz[i][j] = predictor.predict(poly.transform([predictData]))[0]
            zz.reshape(xx.shape)
            cSpace = np.linspace(min(Graphing.array[:,-1]), max(Graphing.array[:,-1]), 10)
            cs = plt.contourf(xx, yy, zz, levels=cSpace)
            cbar = plt.colorbar(cs)

        # Plot details
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()


    def HorizontalPredictionGraph():
        assert not Graphing.array is None, "Need to fit data points; use Graphing.FitData"
        #Hori_shots append (horz_angle_between shooter and target, distance to target, target's tangential velocity, aiming_yaw)
        poly = PolynomialFeatures(2, include_bias=False).fit(Graphing.array[:,1:-1])
        predictor = LinearRegression().fit(poly.transform(Graphing.array[:,1:-1]), Graphing.array[:,-1])
        xSpace = np.linspace(0, Graphing.array[:,1].max(), 100)
        ySpace = np.linspace(Graphing.array[:,2].min(), Graphing.array[:,2].max(), 100)
        xx, yy = np.meshgrid(xSpace, ySpace)
        zz = np.zeros(xx.shape)
        for i in range(xx.shape[0]):
            for j in range(xx.shape[1]):
                zz[i][j] = predictor.predict(poly.transform([[xx[i,j], yy[i,j]]]))[0]
        zz.reshape(xx.shape)
        cs = plt.contourf(xx, yy, zz, levels=[10*i for i in range(-18,19)])
        cbar = plt.colorbar(cs)
        cbar.ax.set_ylabel("Desired Horizontal angle")
        plt.title("Horizontal Angle Regression Predictions")
        plt.xlabel("Distance")
        plt.ylabel("Tangential Velocity")
        plt.show()

    def ErrorGraph():
        assert not Graphing.errors is None, "Need to fit errors; use Graphing.FitErrors"
        plt.scatter(range(Graphing.errors.shape[0]), Graphing.errors)
        plt.title("Errors for each shot")
        plt.xlabel("Arrow shot")
        plt.ylabel("Error")
        plt.show()

    def AccuracyGraph():
        assert not Graphing.errors is None, "Need to fit errors; use Graphing.FitErrors"
        accuracies = []
        for i in range(5, len(Graphing.errors)):
            shots = Graphing.errors[i-5:i]
            hit_shots = shots[shots<2]
            accuracies.append(len(hit_shots) / len(shots))
        plt.plot(np.arange(5, len(Graphing.errors)), accuracies)
        plt.title("Accuracy over last 5 shots")
        plt.xlabel("Last shot")
        plt.show()


    def RegressionLine():
        poly = PolynomialFeatures(1, include_bias=False).fit(Graphing.array[:,0:1])
        predictor = LinearRegression().fit(poly.transform(Graphing.array[:,0:1]), Graphing.array[:,-1])
        xx = np.linspace(-180, 180, 100)
        yy = np.zeros(100)
        for i in range(len(xx)):
            yy[i] = predictor.predict(poly.transform([[xx[i]]]))[0]
        plt.plot(xx, yy, color='blue',linewidth=2,label="Predicted delta angle")
        plt.plot(xx,xx, color='green',label="y=x")
        plt.legend()
        plt.title("Horizontal Angle Regression Predictions")
        plt.xlabel("Delta horizontal angle")
        plt.ylabel("Predicted delta angle")
        plt.show()
