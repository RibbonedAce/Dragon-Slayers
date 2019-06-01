import numpy as np
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

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

    def PredictionGraph():
        assert not Graphing.array is None, "Need to fit data points; use Graphing.FitData"
        poly = PolynomialFeatures(2, include_bias=False).fit(Graphing.array[:,:-1])
        predictor = LinearRegression().fit(poly.transform(Graphing.array[:,:-1]), Graphing.array[:,-1])
        xSpace = np.linspace(0, Graphing.array[:,0].max(), 100)
        ySpace = np.linspace(0, Graphing.array[:,1].max(), 100)
        xx, yy = np.meshgrid(xSpace, ySpace)
        zz = np.zeros(xx.shape)
        for i in range(xx.shape[0]):
            for j in range(xx.shape[1]):
                zz[i][j] = predictor.predict(poly.transform([[xx[i,j], yy[i,j]]]))[0]
        zz.reshape(xx.shape)
        cs = plt.contourf(xx, yy, zz, levels=[5*i for i in range(10)])
        cbar = plt.colorbar(cs)
        cbar.ax.set_ylabel("Vertical angle")
        plt.title("Vertical Angle Regression Predictions")
        plt.xlabel("Distance")
        plt.ylabel("Elevation")
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
