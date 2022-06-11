from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsMarkerSymbol
from qgis.core import QgsPalLayerSettings
from qgis.core import QgsProject
from qgis.utils import iface
from qgis.core import QgsVectorLayerSimpleLabeling

import processing
import os



class Labelpoi(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('SelectPOIs', 'Select POIs', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('LayoutName', 'Type the layout name ', defaultValue= None, multiLine = False))
        self.addParameter(QgsProcessingParameterFolderDestination('Output2', 'Select OUTPUT folder', defaultValue= None))


    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}
        
        output_path = parameters['Output2']
        # Create grid
        alg_params = {
            'CRS': 'ProjectCrs',
            'EXTENT': parameters['SelectPOIs'],
            'HOVERLAY': 0,
            'HSPACING': 16.6,
            'TYPE': 2,
            'VOVERLAY': 0,
            'VSPACING': 16.6,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CreateGrid'] = processing.run('native:creategrid', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Extract by location
        alg_params = {
            'INPUT': outputs['CreateGrid']['OUTPUT'],
            'INTERSECT': parameters['SelectPOIs'],
            'PREDICATE': [0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

 
        # Add field to attributes table
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'IND',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,
            'INPUT': outputs['ExtractByLocation']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AddFieldToAttributesTable'] = processing.run('native:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        
        # Field calculator
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'IND',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,
            'FORMULA': ' @row_number',
            'INPUT': outputs['AddFieldToAttributesTable']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        # Export atlas layout as image
        alg_params = {
            'ANTIALIAS': True,
            'COVERAGE_LAYER': outputs['FieldCalculator']['OUTPUT'],
            'DPI': 100,
            'EXTENSION': 11,
            'FILENAME_EXPRESSION': '\'output_\'||@atlas_featurenumber',
            'FILTER_EXPRESSION': '',
            'FOLDER': os.path.join(output_path),
            'GEOREFERENCE': True,
            'INCLUDE_METADATA': False,
            'LAYERS': None,
            'LAYOUT': parameters['LayoutName'],
            'SORTBY_EXPRESSION': '',
            'SORTBY_REVERSE': False
        }
        outputs['ExportAtlasLayoutAsImage'] = processing.run('native:atlaslayouttoimage', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        folder = os.listdir(output_path)
        
        listaFin = []
        
        decoy = 1
        for file in folder:
            if file.endswith(".tiff"):
            
            # Polygonize (raster to vector)
                alg_params = {
                    'BAND': 1,
                    'EIGHT_CONNECTEDNESS': True,
                    'EXTRA': '',
                    'FIELD': 'DN',
                    'INPUT': ''+output_path+'/output_'+str(decoy)+'.tiff',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['PolygonizeRasterToVector'] = processing.run('gdal:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
                # Extract by attribute
                alg_params = {
                    'FIELD': 'DN',
                    'INPUT': outputs['PolygonizeRasterToVector']['OUTPUT'],
                    'OPERATOR': 5,
                    'VALUE': 230,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
                # Dissolve
                alg_params = {
                    'FIELD': [''],
                    'INPUT': outputs['ExtractByAttribute']['OUTPUT'],
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                
                # Polygons to lines
                alg_params = {
                    'INPUT': outputs['Dissolve']['OUTPUT'],
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                    #'OUTPUT': os.path.join(output_path, 'l'+str(decoy)+'.shp')
                }
                outputs['PolygonsToLines'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                
                listaFin.append(outputs['PolygonsToLines']['OUTPUT'])

                decoy  += 1
                #if decoy == 5:
                 #   break

        # Merge vector layers
        alg_params = {
            'CRS': None,
            'LAYERS': listaFin,
            'OUTPUT': os.path.join(output_path, 'Label_IQMaps.shp')
        }
        outputs['MergeVectorLayers'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        

        #coy=1
        #for file in folder:
            #os.remove(''+output_path+'/output_'+str(coy)+'.tiff')
            #os.remove(''+output_path+'/output_'+str(coy)+'.tfw')
                
            #if file.endswith(".aux"):
            #    os.remove(''+output_path+'/output_'+str(coy)+'.aux')
           # coy += 1

        return results

    def name(self):
        return 'Label POI for IQMaps'

    def displayName(self):
        return 'Label POI for IQMaps'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Labelpoi()
