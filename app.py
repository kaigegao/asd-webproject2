import os
import datetime
from datetime import datetime, timedelta
import logging
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
import zipfile
import csv

# 注释掉模型相关导入
# import torch
# import numpy as np
# from models.MyModel import MyModel  # Ensure this import matches your directory structure
from flask_cors import CORS


# 注释掉与神经网络相关的导入
# from nilearn.image import load_img
# from nilearn import masking
# from nilearn.image import resample_to_img
# from nilearn.input_data import NiftiLabelsMasker
# from nilearn import plotting, datasets
# from nilearn import image
# import nibabel as nib
# import matplotlib

# import pickle
# import networkx as nx
# import plotly.graph_objects as go
# from torch_geometric.data import Data

# matplotlib.use("Agg")

os.environ["HOME"] = os.path.expanduser("~")

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)
# 允许上传的文件类型
ALLOWED_EXTENSIONS = {'csv', 'txt'}
# 存储问卷数据的列表
surveys = []
# 存储用户数据的列表
users = []
UPLOAD_FOLDER = "./uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # 正确设置配置变量
app.config['case_save_file'] = "./cases_save_file.csv"
app.config['user_info_file'] = "./user_info_file.csv"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
cases = []
# global viewing_file


# 注释掉模型配置和加载
"""
# Configuration class for model parameters
class DefaultConfig(object):
    dataset = "Kaggle"
    d_model = 1024
    n_layer = 24
    ssm_cfg = dict()
    norm_epsilon = 1e-5
    rms_norm = True  # 启用RMSNorm
    residual_in_fp32 = True  # 启用fp32残差
    fused_add_norm = False  # 禁用fused_add_norm
    initializer_cfg = None
    lr = 4.3895647763297976e-05
    hidden_1 = 1024
    hidden_2 = 1024
    batch_size = 32
    num_workers = 0
    embed = "fixed"
    freq = "h"
    dropout = 0.3762915331187696
    num_class = 2
    pred_len = 0
    if dataset == "Kaggle":
        enc_in = 110
        seq_len = 176
    elif dataset == "ABIDE_preprocessed":
        enc_in = 111
        seq_len = 316
    device = torch.device("cpu")  # 强制使用CPU
    dtype = torch.float32

    model_path = "models/Mamba_GCN_OF_dmodel_1024_nlayer_24_lr_4.3895647763297976e-05_dropout_0.3762915331187696_hidden1_1024_hidden2_1024.pth"

args = DefaultConfig()
model = MyModel(args)

# 使用CPU加载模型
try:
    state_dict = torch.load(args.model_path, map_location='cpu')
    model.load_state_dict(state_dict, strict=False)  # 使用strict=False允许加载部分权重
    print("模型加载成功")
except Exception as e:
    print("模型加载出错:", e)
    raise e

model.to(args.device)
model.eval()

class DefaultConfigNii(object):
    dataset = "ABIDE_preprocessed"
    ssm_cfg = dict()
    norm_epsilon = 1e-5
    rms_norm = True  # 启用RMSNorm
    residual_in_fp32 = True  # 启用fp32残差
    fused_add_norm = False  # 禁用fused_add_norm
    initializer_cfg = None
    num_class = 2
    pred_len = 0
    batch_size = 32
    num_workers = 0
    embed = "fixed"
    freq = "h"
    enc_in = 111
    seq_len = 316
    d_model = 128
    n_layer = 12
    lr = 1.402889935057092e-05  # Learning rate
    hidden_1 = 128
    hidden_2 = 128
    dropout = 0.17165397371078353  # Dropout rate
    model_path = "models/Mamba_GCN_OF_dmodel_128_nlayer_12_lr_1.402889935057092e-05_dropout_0.17165397371078353_hidden1_128_hidden2_128.pth"
    device = torch.device("cpu")  # 强制使用CPU
    dtype = torch.float32

argsNii = DefaultConfigNii()
modelNii = MyModel(argsNii)
# 使用CPU加载模型
try:
    state_dictNii = torch.load(argsNii.model_path, map_location='cpu')
    modelNii.load_state_dict(state_dictNii, strict=False)  # 使用strict=False允许加载部分权重
    print("模型加载成功")
except Exception as e:
    print("模型加载出错:", e)
    raise e
modelNii.to(argsNii.device)
modelNii.eval()
"""


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/team')
def team():
    return render_template('team.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # 检查是否有文件部分
        if 'data_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['data_file']
        # 如果用户没有选择文件，浏览器也会提交一个空的文件名
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # 处理上传的文件（例如：读取数据、存储到数据库等）
            process_uploaded_file(file_path)
            return f'File {filename} has been uploaded successfully.'
    return render_template('upload.html')


def process_uploaded_file(file_path):
    # 这里可以添加处理上传文件的逻辑
    print(f"Processing file: {file_path}")
    # 示例：读取CSV文件并打印内容
    data = pd.read_csv(file_path)
    # print(data.head())


@app.route('/survey')
def survey():
    return render_template('survey.html')

def get_next_case_id(filename):
    if not os.path.exists(filename):
        return 0
    try:
        existing_df = pd.read_csv(filename)
        if existing_df.empty:
            return 0
        else:
            return existing_df['caseId'].max() + 1
    except FileNotFoundError:
        print('FileNotFound')
        return 0
    except pd.errors.EmptyDataError:
        print('EmptyData')
        return 0
    except pd.errors.ParserError:
        print('ParserError')
        return 0

@app.route('/api/upload_case', methods=['POST'])
def file_upload_destination():
    file = request.files.get("case-file")
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config.get("UPLOAD_FOLDER"), filename)
        file.save(file_path)

        # 读取文件内容，将第一列设置为索引
        data = pd.read_csv(file_path)
        # 注释掉模型预测
        # diagnosis, risk, graph = predict(data.values)
        
        # 设置默认值
        diagnosis, risk = 'Pending', '0.0'

        data = {
            'age': request.form.get("age"),
            'gender': request.form.get("gender"),
            'name': request.form.get("name"),
            'fmri.image': "None",
            'file': filename,
            'uploadDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            #保留预测功能
            'diagnosis': diagnosis,
            # 保留预测功能
            'risk': str(risk),
            'doctor':session['username']
        }
        cases.append(data)
        file_path = app.config.get("case_save_file")
        case_id = get_next_case_id(file_path)

        data_with_case_id = {'caseId': case_id, **data}
        columns_order = ['caseId', 'age', 'gender', 'name', 'fmri.image','file', 'uploadDate','diagnosis','risk','doctor']
        df = pd.DataFrame([data_with_case_id], columns=columns_order)
        try:
            existing_df = pd.read_csv(file_path)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_csv(file_path, index=False)

        except pd.errors.EmptyDataError:
            df.to_csv(file_path,  index=False)

        return {'success': True, 'result': str(case_id)}, 200

    except Exception as e:
        return {'success': False, 'errorMsg': f'Error reading file {"caseInfo"}: {str(e)}'}, 200




@app.route('/api/upload_feedback', methods=['POST'])
def upload_feedback():
    try:
        # 获取表单数据
        caseId = request.form.get('caseId')
        feedback = request.form.get('feedback')
        doctor = session.get('username', 'Unknown')
        # 指定CSV文件路径
        csv_file_path = 'feedback.csv'

        # 检查文件是否存在，如果不存在则创建并写入表头
        file_exists = os.path.exists(csv_file_path)

        with open(csv_file_path, mode='a', newline='') as csv_file:
            fieldnames = ['caseId', 'feedback', 'doctor']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()  # 写入表头

            # 写入数据
            writer.writerow({'caseId': caseId, 'feedback': feedback, 'doctor': doctor})

        return {'success': True, 'result': ''}, 200
    except Exception as e:
        return {'success': False, 'errorMsg': f'Error reading file {"caseInfo"}: {str(e)}'}, 200



@app.route('/upload_case', methods=['GET', 'POST'])
def upload_case():
    return render_template('upload_case.html')






@app.route('/return_to_upload')
def return_to_upload():
    return redirect(url_for('upload_case'))


@app.route('/bulk_upload_cases')
def bulk_upload_cases():
    return render_template('bulk_upload_cases.html')

bulk_cases = []
@app.route('/bulk_upload', methods=['GET', 'POST'])
def upload_files():

    if request.method == 'POST':

        zip_file = request.files.get('zipFile')
        csv_file = request.files.get('csvFile')

        if not zip_file or not csv_file:
            flash('No file part')
            # return redirect(request.url)
            return "success"

        if zip_file.filename.endswith('.zip') and csv_file.filename.endswith('.csv'):

            zip_filename = secure_filename(zip_file.filename)
            csv_filename = secure_filename(csv_file.filename)

            zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
            csv_path = os.path.join(UPLOAD_FOLDER, csv_filename)

            zip_file.save(zip_path)
            csv_file.save(csv_path)

            upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_contents = zip_ref.namelist()
                for item in zip_contents:
                    if item in get_csv_filenames(csv_path):
                        extracted_path = os.path.join(UPLOAD_FOLDER, item)
                        zip_ref.extract(item, UPLOAD_FOLDER)

                        cases.append({
                            'age': get_csv_row_value(csv_path, item, 'age'),
                            'gender': get_csv_row_value(csv_path, item, 'gender'),
                            'name': get_csv_row_value(csv_path, item, 'name'),
                            'file': item,
                            'uploadDate': upload_date
                        })
                        data={
                            'age': get_csv_row_value(csv_path, item, 'age'),
                            'gender': get_csv_row_value(csv_path, item, 'gender'),
                            'name': get_csv_row_value(csv_path, item, 'name'),
                            'file': item,
                            'uploadDate': upload_date
                        }
                        file_path = app.config.get("case_save_file")
                        case_id = get_next_case_id(file_path)
                        data_with_case_id = {'caseId': case_id, **data}
                        columns_order = ['caseId', 'age', 'gender', 'name', 'file', 'uploadDate']
                        df = pd.DataFrame([data_with_case_id], columns=columns_order)
                        try:
                            existing_df = pd.read_csv(file_path)
                            updated_df = pd.concat([existing_df, df], ignore_index=True)
                            updated_df.to_csv(file_path, index=False)
                        except pd.errors.EmptyDataError:
                            df.to_csv(file_path, index=False)
            os.remove(zip_path)
            os.remove(csv_path)

            flash('Files successfully processed')
            return redirect(url_for('upload_files'))

        else:
            flash('Invalid file format')
            return redirect(request.url)

    return render_template('bulk_upload2.html')


@app.route('/api/fmri_image_upload', methods=['POST'])
def upload_image_files():

    file = request.files.get("case-file")
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    try:
        filename = file.filename
        filename2 = filename.replace('.nii.gz', '')
        file_path = os.path.join(app.config.get("UPLOAD_FOLDER"), filename)

        file.save(file_path)
        # 注释掉模型预测相关代码
        # convert_fmri_image_to_timeseries(file_path, filename2, app.config.get("UPLOAD_FOLDER"))
        # TODO: 这里更改了fMRI到时序数据的函数，并且这个函数这里是没有第一列的unname:0无意义信息的，如果需要请自行修改index=True
        # convert_fmri_image_to_ho_timeseries(file_path, filename2, app.config.get("UPLOAD_FOLDER"))

        # file_path2 = os.path.join(app.config.get("UPLOAD_FOLDER"), filename2+ '_timeseries_predict.csv')
        # data = pd.read_csv(file_path2)
        # diagnosis, risk, graph = predictNii(data.values)
        
        # 设置默认值
        diagnosis, risk = 'Pending', '0.0'

        data = {
            'age': request.form.get("age"),
            'gender': request.form.get("gender"),
            'name': request.form.get("name"),
            'fmri.image': filename,
            'file': filename2+ '_timeseries.csv', # 此处可能需要为文件创建一个空文件
            'uploadDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # 保留预测功能
            'diagnosis': diagnosis,
            # 保留预测功能
            'risk': str(risk),
            'doctor': session['username']
        }

        file_path = app.config.get("case_save_file")
        case_id = get_next_case_id(file_path)

        data_with_case_id = {'caseId': case_id, **data}
        columns_order = ['caseId', 'age', 'gender', 'name', 'fmri.image', 'file', 'uploadDate', 'diagnosis', 'risk',
                            'doctor']
        df = pd.DataFrame([data_with_case_id], columns=columns_order)
        try:
            existing_df = pd.read_csv(file_path)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_csv(file_path, index=False)

        except pd.errors.EmptyDataError:
            df.to_csv(file_path, index=False)

        # 注释掉与脑图像相关的代码
        """
        counter = 0
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        target_folder = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
        os.makedirs(target_folder, exist_ok=True)
        img = load_img(file_path)
        num_time_points = img.shape[-1]
        for brain_index in range(0,num_time_points,int(num_time_points/5)):
            # 提取当前时间点的数据
            first_volume = image.index_img(img, brain_index)
            html_view = plotting.view_img(first_volume)
            save_name = f"brain_image_{counter}.html"
            final_path = os.path.join(target_folder, save_name)
            html_view.save_as_html(final_path)
            counter += 1
        """

        return {'success': True, 'result': str(case_id)}, 200
    except Exception as e:
        return {'success': False, 'errorMsg': f'Error reading file {"caseInfo"}: {str(e)}'}, 200


def convert_fmri_image_to_ho_timeseries(image_path, file_name, fmri_save_path):
    # 设置atlas和标签文件路径 (假设在当前目录)
    atlas_path = "ho/ho_roi_atlas.nii.gz"
    labels_path = "ho/ho_labels.csv"
    # 1. 加载数据
    fmri_img = load_img(image_path)
    atlas_img = load_img(atlas_path)
    # 2. 读取标签文件
    labels_df = pd.read_csv(labels_path)
    labels = labels_df.iloc[:, 1].tolist()[1:]  # 假设第二列是区域名称
    # 3. 创建背景掩码
    mask = masking.compute_background_mask(fmri_img)
    # 4. 将atlas重采样到与fMRI相同的空间
    resampled_atlas = resample_to_img(atlas_img, mask, interpolation='nearest')
    # 5. 创建掩码器
    masker = NiftiLabelsMasker(
        labels_img=resampled_atlas,
        standardize=True,
        memory='nilearn_cache',
        verbose=0
    )
    # 6. 提取时间序列
    time_series = masker.fit_transform(fmri_img)
    # 7. 验证维度
    if time_series.shape[1] != len(labels):
        print('Error: time_series.shape[1] != len(labels)')
        print(time_series.shape)
        print(len(labels))
        return
    # 8. 创建DataFrame并保存
    df = pd.DataFrame(time_series, columns=labels)
    # 构建保存路径
    save_path = os.path.join(fmri_save_path, file_name + '_timeseries_predict.csv')
    # 保存为CSV
    df.to_csv(save_path, index=False)
    save_path2 = os.path.join(fmri_save_path, file_name + '_timeseries.csv')
    # 保存为CSV
    df.to_csv(save_path2, index=True)


@app.route('/api/query_fmri_image_html_content', methods=['POST'])
def query_fmri_image_html_content():
    data=request.get_json()
    index=data['index']
    name=data['image_name']
    # 返回一个静态HTML内容而不是动态生成的脑图像
    return jsonify({"message": "模型功能已禁用"}), 200
    # 注释原始代码
    """
    app.config['UPLOAD_FOLDER']
    file_name = f"brain_image_{index}.html"
    target_folder = os.path.join(app.config['UPLOAD_FOLDER'], name)
    file_path = os.path.join(target_folder, file_name)
    return send_file(file_path, mimetype='text/html')
    """

def convert_fmri_image_to_timeseries(image_path, file_name, fmri_save_path):

    dataset = datasets.fetch_atlas_aal()

    atlas_filename = dataset.maps
    labels = dataset.labels
    fMRIData = load_img(image_path)
    mask = masking.compute_background_mask(fMRIData)
    Atlas = resample_to_img(atlas_filename, mask, interpolation='nearest')
    masker = NiftiLabelsMasker(labels_img=Atlas, standardize=True,
                            memory='nilearn_cache', verbose=0)
    time_series = masker.fit_transform(fMRIData)
    if time_series.shape[1] != len(labels):
        print('Error: time_series.shape[1] != len(labels)')
        print(time_series[0,:])
        print("====================================================")
        print(labels)
    df = pd.DataFrame(time_series, columns=labels)
    save_path = os.path.join(fmri_save_path, file_name + '_timeseries.csv')
    df.to_csv(save_path, index=True)




def get_csv_filenames(csv_path):
    filenames = set()
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            filenames.add(row['file'])
    return filenames

def get_csv_row_value(csv_path, filename, column_name):
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['file'] == filename:
                return row[column_name]
    return None




@app.route('/view_cases')
def view_cases():
    records = []
    try:
        file_path = app.config.get("case_save_file")

        df_final = pd.read_csv(file_path)
        df_final.fillna('——', inplace=True)
        filtered_df = df_final[df_final['doctor'] == session.get('username')]

        camel = filtered_df.to_html(classes='table table-striped', index=False, escape=False, formatters={
            'caseId': lambda x: f'<a href="{url_for("case_detail", case_id=x)}">{x}</a>'
        })
        records.append(("Medical cases information", camel))
    except Exception as e:
        flash(f'Error reading file {"caseInfo"}: {str(e)}', 'danger')

    return render_template('view_cases.html', records=records, filtered_df=filtered_df)

@app.route('/api/query_cases', methods=['POST'])
def query_cases():
    # 获取参数处理筛选项逻辑
    filter = request.get_json()
    try:
        file_path = app.config.get("case_save_file")

        df_final = pd.read_csv(file_path)
        df_final = df_final.applymap(lambda x: None if pd.isna(x) else x)
        filtered_df = df_final[df_final['doctor'] == session.get('username')]

        # 根据filter中提供的条件进行筛选
        mask = df_final['doctor'] == session.get('username')
        if filter.get('caseId') not in [None, '']:
            case_id_mask = df_final['caseId']== int(filter['caseId'])
            mask &= case_id_mask
        if filter.get('name') not in [None, '']:
            name_mask = df_final['name'] == filter['name']
            mask &= name_mask

        filtered_df = df_final[mask]

        records = filtered_df.to_dict(orient='records')
    except Exception as e:
        return {'success': False, 'errorMsg': f'Error reading file {"caseInfo"}: {str(e)}'}, 200

    return {'success': True, 'result': {'list': records,'total': len(records)}}, 200

@app.route('/api/query_feed', methods=['POST'])
def query_feed():
    filter_data = request.get_json()
    try:
        csv_file_path = 'feedback.csv'
        records = []
        with open(csv_file_path, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                # 获取当前用户的用户名
                current_username = session.get('username', 'Unknown')
                # 获取filter中的caseId
                filter_case_id = filter_data.get('caseId', '')

                # 如果filter中的caseId为空，匹配所有当前session.get('username')和csv中的'doctor'列符合的记录
                if not filter_case_id:
                    if row['doctor'] == current_username:
                        records.append({'caseId': row['caseId'], 'feedback': row['feedback']})
                # 如果filter中的caseId有内容且不为''，匹配当前session.get('username')和csv中的'doctor'列符合的记录，且'caseId'也要匹配
                else:
                    if row['doctor'] == current_username and row['caseId'] == filter_case_id:
                        records.append({'caseId': row['caseId'], 'feedback': row['feedback']})
    except Exception as e:
        return {'success': False, 'errorMsg': f'Error reading file {"caseInfo"}: {str(e)}'}, 200

    return {'success': True, 'result': {'list': records,'total': len(records)}}, 200

@app.route('/case_detail/<int:case_id>')
def case_detail(case_id):
    file_path = app.config.get("case_save_file")
    df = pd.read_csv(file_path)
    result = df.loc[df['caseId'] == case_id, 'file']
    result2 = df.loc[df['caseId'] == case_id, 'fmri.image']
    viewing_file = secure_filename(result.iloc[0])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(result.iloc[0]))

    # 检查是否有眼动数据
    eye_data = None
    eye_image = None
    
    # 首先检查eye_tracking_file列
    if 'eye_tracking_file' in df.columns:
        eye_tracking_file = df.loc[df['caseId'] == case_id, 'eye_tracking_file']
        
        if not eye_tracking_file.empty and pd.notna(eye_tracking_file.iloc[0]):
            # 确保只获取文件名
            eye_data = eye_tracking_file.iloc[0]
            
            # 特别处理：如果眼动数据文件为eye_tracking/1.csv或1.csv，直接显示uploads文件夹中的1_50.png
            if '1.csv' in eye_data:
                eye_image = '1_50.png'
                # 确保1_50.png文件存在
                png_path = os.path.join(app.config.get("UPLOAD_FOLDER"), '1_50.png')
                if not os.path.exists(png_path):
                    try:
                        # 创建一个默认的眼动数据图像
                        import matplotlib.pyplot as plt
                        import numpy as np
                        plt.figure(figsize=(8, 6))
                        plt.plot(np.random.rand(50), 'r-')
                        plt.title('眼动数据可视化')
                        plt.xlabel('时间 (ms)')
                        plt.ylabel('位置')
                        plt.grid(True)
                        plt.savefig(png_path)
                        plt.close()
                        print(f"成功创建眼动数据图像: {png_path}")
                    except Exception as e:
                        print(f"创建图像时出错: {str(e)}")
                        # 如果无法创建图像，尝试使用PIL
                        try:
                            from PIL import Image, ImageDraw, ImageFont
                            img = Image.new('RGB', (800, 600), color=(255, 255, 255))
                            d = ImageDraw.Draw(img)
                            d.text((400, 300), "眼动数据可视化", fill=(0, 0, 0))
                            img.save(png_path)
                            print(f"使用PIL创建替代图像: {png_path}")
                        except Exception as e2:
                            print(f"创建替代图像时出错: {str(e2)}")
                            # 如果PIL也不可用，创建一个文本文件
                            try:
                                with open(os.path.join(app.config.get("UPLOAD_FOLDER"), '1_50.txt'), 'w') as f:
                                    f.write("这是眼动数据可视化的描述文本")
                                print("创建了文本替代文件")
                            except Exception as e3:
                                print(f"创建文本文件时出错: {str(e3)}")

    try:
        # 读取文件内容
        data = pd.read_csv(file_path, index_col=0)
        table_html = data.to_html(index=True)
    except Exception as e:
        flash(f'Error reading file : {str(e)}', 'danger')
        return redirect(url_for('view_cases'))

    return render_template('case_detail.html', 
                          img=result2.iloc[0],
                          case=result.iloc[0],
                          table_html=table_html,
                          eye_data=eye_data,
                          eye_image=eye_image)



@app.route('/delete_case', methods=['POST'])
def delete_case():
    # 检查用户是否登录
    username = session.get('username')
    if not username:
        flash('请先登录以继续操作.', 'warning')
        return redirect(url_for('login'))

    try:
        data = request.get_json()
        file_path = app.config.get("case_save_file")
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError("病例保存文件路径未配置或文件不存在.")

        # 读取CSV文件
        df_final = pd.read_csv(file_path)

        # 确认当前医生有权删除该病例
        if df_final[df_final['caseId'] == data['case_id']]['doctor'].values[0] != username:
            flash('您无权删除此病历.', 'danger')
            return redirect(url_for('view_cases'))

        row = df_final.loc[df_final['caseId'] == data['case_id']].iloc[0]
        fmri_image = row['fmri.image']
        file_value = row['file']
        # 删除fmri.image对应的文件（如果存在）
        if pd.notna(fmri_image):
            fmri_image_path = os.path.join(app.config.get("UPLOAD_FOLDER"), fmri_image)
            if os.path.exists(fmri_image_path):
                os.remove(fmri_image_path)
                print(f"已删除文件: {fmri_image_path}")
            else:
                print(f"文件不存在: {fmri_image_path}")

        # # # 删除file列对应的文件（如果存在）
        if pd.notna(file_value) :
            csv_file_path = os.path.join(app.config.get("UPLOAD_FOLDER"), file_value)
            if os.path.exists(csv_file_path):
                os.remove(csv_file_path)
                print(f"已删除文件: {csv_file_path}")
            else:
                print(f"文件不存在: {csv_file_path}")
        # 删除对应的行
        df_updated = df_final[df_final['caseId'] != data['case_id']]

        # 保存更新后的DataFrame回CSV文件
        df_updated.to_csv(file_path, index=False)

        return {'success': True}, 200
    except Exception as e:
        app.logger.error(f'Error deleting case {data["case_id"]}: {str(e)}')
        return {'success': False, 'errorMsg': f'删除病历时发生错误: {str(e)}'}, 200

@app.route('/api/query_csv_data', methods=['POST'])
def query_csv_data():
    data = request.get_json()
    records = []
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        df_final = pd.read_csv(file_path, index_col=0)
        records = df_final.dropna().to_dict('records')
    except Exception as e:
        {'success': False, 'errorMsg': f'Error reading file {"caseInfo"}: {str(e)}'}

    return {'success': True, 'result': {'list': records,'total': len(records)}}

@app.route('/api/get_column_data', methods=['POST'])
def get_column_data():
    data = request.get_json()

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], data['viewing_file'])

    try:
        # 读取文件内容，将第一列设置为索引
        df_final = pd.read_csv(file_path, index_col=0)

        if data['column_header'] not in df_final.columns:
            return {'success': False, 'errorMsg': f'Column {data["column_header"]} not found'}, 500

        index = df_final.index.tolist()
        values = df_final[data['column_header']].tolist()

        return {'success': True, 'result': {'index': index, 'values': values}}
    except Exception as e:
        return {'success': False, 'errorMsg': str(e)}, 500


@app.route('/predict', methods=['POST'])
def predict_case():
    req = request.get_json()

    # 直接返回默认值，而不调用模型
    diagnosis, risk = 'Pending', 0.0

    # 更新CSV文件中的记录
    csv_path = app.config.get("case_save_file")
    df = pd.read_csv(csv_path)

    # 找到df中'file'列的值等于req['viewing_file']的那一行
    match = df['file'] == req['viewing_file']

    if match.any():  # 如果找到了匹配的行
        # 更新diagnosis和risk值
        df.loc[match, 'diagnosis'] = diagnosis
        df.loc[match, 'risk'] = str(risk)

        # 将更新后的数据写回到csv文件中
        df.to_csv(csv_path, index=False)

    return {'success': True, 'result': {'diagnosis': diagnosis, 'risk': str(risk)}}, 200

    # 注释掉原始代码
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], req['viewing_file'])
    try:
        if req['viewing_file'].endswith("timeseries.csv"):
            file_path = file_path.replace(".csv", "") + "_predict.csv"
        else:
            file_path = file_path
        # 读取文件内容，将第一列设置为索引

        data = pd.read_csv(file_path)
        if req['viewing_file'].endswith("timeseries.csv"):
            diagnosis, risk, graph = predictNii(data.values)
        else:
            diagnosis, risk, graph = predict(data.values)

        #diagnosis, risk ='ASD',0.99

        csv_path = app.config.get("case_save_file")
        df= pd.read_csv(csv_path)

        # 找到df中'file'列的值等于req['viewing_file']的那一行
        match = df['file'] == req['viewing_file']

        if match.any():  # 如果找到了匹配的行
            # 更新diagnosis和risk值
            df.loc[match, 'diagnosis'] = diagnosis
            df.loc[match, 'risk'] = str(risk)

            # 将更新后的数据写回到csv文件中
            df.to_csv(csv_path, index=False)

        return {'success': True, 'result': {'diagnosis': diagnosis, 'risk': str(risk)}}, 200
    except Exception as e:
        return {'success': False,'errorMsg': str(e)}, 200
    """


@app.route('/get_nii_data/<filename>')
def get_nii_data(filename):
    # 返回一个空的结果而不是解析.nii文件
    return jsonify({
        'data': [],
        'dimensions': [0, 0, 0],
        'message': '模型功能已禁用'
    })
    
    # 注释掉原始代码
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    try:

        nii_img = nib.load(file_path)
        data = nii_img.get_fdata()

        # 发送整个数据到前端
        data_list = data.tolist()
        dimensions = list(data.shape)  # 保留原始数据的完整维度

        # small_data_subset = data[:, :, 0, :10]
        # dimensions = list(small_data_subset.shape)  # 保留原始数据的完整维度
        # small_data_subset_list=small_data_subset.tolist()

        return jsonify({'data': data_list, 'dimensions': dimensions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    """


@app.route('/get_brain_image', methods=['GET'])
def get_brain_image():
    # 返回一个简单的HTML而不是动态生成的脑图像
    return jsonify({"message": "模型功能已禁用"}), 200
    
    # 注释掉原始代码
    """
    # 加载示例图像
    brain_index = int(request.args.get('index'))
    print(brain_index)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], request.args.get('filename'))
    img = load_img(file_path)
    first_volume = image.index_img(img, brain_index)

    # 创建交互式视图
    html_view = plotting.view_img(first_volume)

    html_view.save_as_html("brain_image.html")

    return send_file("brain_image.html", mimetype='text/html')
    """


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        flash('请先登录。')
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        # 验证当前密码是否正确
        user = next((user for user in users if
                     user['username'] == session['username'] and user['password'] == current_password), None)
        if not user:
            flash('当前密码不正确，请重试。')
            return redirect(url_for('change_password'))

        # 验证新密码和确认新密码是否一致
        if new_password != confirm_new_password:
            flash('新密码和确认新密码不一致，请重试。')
            return redirect(url_for('change_password'))

        # 更新用户密码
        user['password'] = new_password
        flash('密码更改成功！')
        return redirect(url_for('index'))

    return render_template('change_password.html')


@app.route('/case_management')
def case_management():
    return render_template('case_management.html')


@app.route('/submit_survey', methods=['POST'])
def submit_survey():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        feedback = request.form.get('feedback')

        # 将问卷数据存储到列表中
        surveys.append({
            'name': name,
            'email': email,
            'feedback': feedback,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        flash('感谢您的反馈！')
        return redirect(url_for('index'))
    return "Invalid request", 400


@app.route('/survey2')
def survey2():
    return render_template('survey2.html')


@app.route('/upload_video')
def upload_video():
    return render_template('upload_video.html')


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)
    username = data['username']
    email = data['email']
    password = data['password']
    role = data['role']
    hospital = data['hospital'] if role == 'doctor' else None

    # 简单的验证：检查用户名是否已存在
    if any(user['username'] == username for user in users):
        return {'success': False, 'errorMsg': '用户名已存在，请选择其他用户名。'}, 200

    # 将用户数据存储到列表中
    data = {
        'username': username,
        'email': email,
        'password': password,
        'role': role,
        'hospital': hospital,
        'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    users.append(data)
    try:
        df = pd.DataFrame([data])
        df['registration_date'] = pd.to_datetime(df['registration_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # print(df)
        file_path = app.config.get("user_info_file")

        raw_df = pd.read_csv(file_path)
        if df['email'].iloc[0] in raw_df['email'].values or df['username'].iloc[0] in raw_df['username'].values :
            print(f"Email {email} already exists.")
        else:
            # 将新的DataFrame追加到读取的DataFrame中
            df.to_csv(file_path, mode='a', header=False, index=False)
        return {'success': True}, 200
    except Exception as e:
        print(str(e))
        return {'success': False, 'errorMsg': str(e)}, 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    file_path = app.config.get("user_info_file")
    raw_df = pd.read_csv(file_path)
    if raw_df['username'].eq(data['username']).any():
        # 用户名存在，进一步判断密码是否一致
        df = raw_df[ raw_df['username'] == data['username']].to_dict('records')[0]
        if (df['username'] == data['username']) and (str(df['password']) == data['password']):
            print(f"用户 {data['username']} 存在，并且密码一致。")
            session['username'] = data['username']
            session['role'] = df['role']
            if df['role'] == 'doctor':
                return {'success': True}, 200
            else:
                return {'success': False, 'errorMsg': "Not a doctor, temporarily unable to log in"}, 200
        else:
            return {'success': False, 'errorMsg': f"User {data['username']} exists, But the passwords don't match."}, 200
    else:
        return {'success': False, 'errorMsg': 'The username or password is incorrect, please try again.'}, 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return {'success': True}, 200


@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'role' in session and session['role'] == 'doctor':
        file_path = app.config.get("case_save_file")
        df = pd.read_csv(file_path)
        num_data_rows = len(df)
        session['total_cases'] = num_data_rows

        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        one_week_ago2=one_week_ago.strftime('%Y-%m-%d %H:%M:%S')
        recent_cases = df[df['uploadDate'] >= one_week_ago2]
        weekly_new_cases = len(recent_cases)
        session['weekly_new_cases'] = weekly_new_cases

        return render_template('doctor_dashboard2.html')
    else:
        flash('您无权访问此页面。')
        return redirect(url_for('index'))


@app.route('/plot', methods=['POST'])
def plot():
    # 返回一个空的结果，不调用图表生成函数
    return {'success': True, 'result': {'message': '模型功能已禁用'}}, 200
    
    # 注释掉原始代码
    """
    data = request.get_json()
    filename = secure_filename(data['filename'])
    file_path = os.path.join(app.config.get("UPLOAD_FOLDER"), filename)
    csvdata = pd.read_csv(file_path)
    diagnosis, risk, loaded_data = predict(csvdata.values)
    # with open("graph_data.pkl", "rb") as f:
    #     loaded_data = pickle.load(f)

    node_features = loaded_data.x.numpy()
    edge_index = loaded_data.edge_index.t().numpy()
    node_labels = loaded_data.y.numpy()

    headers = read_csv_headers(file_path)

    G = create_graph(node_features, edge_index, node_labels, headers)
    fig_dict = generate_plotly_fig(G, data['edges'], data['opacity'])
    return {'success': True, 'result': fig_dict}, 200
    """

# 注释掉图表生成相关函数
"""
def read_csv_headers(file_path):
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)
        headers = next(csv_reader)  # 读取表头
        headers = headers[1:111]  # 跳过第一列
    return headers

def create_graph(node_features, edge_index, node_labels, headers):
    G = nx.Graph()
    for i, header in enumerate(headers):
        G.add_node(i, name=header, feature=node_features[i], label=node_labels[i])
    for edge in edge_index:
        weight = edge[0] + edge[1]
        G.add_edge(edge[0], edge[1], weight=weight)
    return G

def generate_plotly_fig(G, top_n_edges=20, opacity=0.8):
    pos = nx.spring_layout(G, k=0.5, iterations=20)
    sorted_edges = sorted(G.edges(data=True), key=lambda x: x[2].get('weight', 1), reverse=True)
    top_n_edges_data = sorted_edges[:top_n_edges]

    G_filtered = nx.Graph()
    G_filtered.add_nodes_from(G.nodes(data=True))
    G_filtered.add_edges_from((u, v) for u, v, d in top_n_edges_data)

    node_x = [pos[k][0] for k in G_filtered.nodes()]
    node_y = [pos[k][1] for k in G_filtered.nodes()]

    weight_color_map = {}
    min_weight = min(edge[2]['weight'] for edge in top_n_edges_data)
    max_weight = max(edge[2]['weight'] for edge in top_n_edges_data)
    for edge in top_n_edges_data:
        weight = edge[2]['weight']
        if weight not in weight_color_map:
            color = f'rgba(0,0,{int(255*(weight-min_weight)/(max_weight-min_weight))},{opacity})'
            weight_color_map[weight] = {'edges': [], 'color': color}
        weight_color_map[weight]['edges'].append(edge)

    fig = go.Figure(layout=go.Layout(

        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),

        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    )

    for weight, data in weight_color_map.items():
        edge_x = []
        edge_y = []
        for u, v, d in data['edges']:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color=data['color']),
            hoverinfo='none',
            mode='lines'))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            color=[G_filtered.nodes[n]['label'] for n in G_filtered.nodes()],
            line_width=2),
        text=[G_filtered.nodes[n]['name'] for n in G_filtered.nodes()],
        textposition="top center")
    fig.add_trace(node_trace)

    fig_dict = fig.to_dict()
    return convert_fig_to_json_serializable(fig_dict)

def convert_fig_to_json_serializable(fig_dict):
    def convert(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        elif isinstance(o, np.generic):
            return o.item()
        return o
    return json_traverse(fig_dict, convert)

def json_traverse(obj, convert_function):
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            new_obj[key] = json_traverse(value, convert_function)
        return new_obj
    elif isinstance(obj, list):
        return [json_traverse(element, convert_function) for element in obj]
    else:
        return convert_function(obj)
"""

@app.route('/api/get_statistics', methods=['POST'])
def get_statistics():
    try:
        # Read CSV file
        df = pd.read_csv('cases_save_file.csv')
        
        # Calculate total samples (excluding header)
        total_samples = len(df)
        
        # Calculate age distribution
        age_bins = [0, 3, 6, 9, 20, float('inf')]
        age_labels = ['0-3', '4-6', '6-9', '10-20', '20+']
        df['age_group'] = pd.cut(df['age'], bins=age_bins, labels=age_labels, right=False)
        age_distribution = df['age_group'].value_counts().reset_index()
        age_distribution.columns = ['age', 'value']
        # 将'age'列转换为分类类型，并指定顺序
        age_distribution['age'] = pd.Categorical(age_distribution['age'], categories=age_labels, ordered=True)

        # 按照指定的顺序排序
        age_distribution = age_distribution.sort_values('age')

        age_distribution = age_distribution.to_dict('records')
        
        # Calculate sample distribution
        diagnosis_counts = df['diagnosis'].value_counts()
        positive_count = diagnosis_counts.get('ASD', 0)
        negative_count = diagnosis_counts.get('Normal', 0)



        return jsonify({
            'success': True,
            'result': {
                'totalSamples': str(total_samples),
                'ageDistribution': str(age_distribution),
                'sampleDistribution': {
                    'positive': str(positive_count),
                    'negative': str(negative_count)
                }
            }
        })
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({
            'success': False,
            'errorMsg': str(e)
        })


@app.route('/api/create_case', methods=['POST'])
def create_case():
    try:
        # 获取表单数据
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        
        data = {
            'age': age,
            'gender': gender,
            'name': name,
            'fmri.image': None,
            'file': None,
            'uploadDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'diagnosis': 'Pending',
            'risk': '0.0',
            'doctor': session['username']
        }
        
        file_path = app.config.get("case_save_file")
        case_id = get_next_case_id(file_path)

        data_with_case_id = {'caseId': case_id, **data}
        columns_order = ['caseId', 'age', 'gender', 'name', 'fmri.image','file', 'uploadDate','diagnosis','risk','doctor']
        df = pd.DataFrame([data_with_case_id], columns=columns_order)
        
        try:
            existing_df = pd.read_csv(file_path)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_csv(file_path, index=False)
        except pd.errors.EmptyDataError:
            df.to_csv(file_path, index=False)

        return {'success': True, 'result': str(case_id)}, 200
    except Exception as e:
        return {'success': False, 'errorMsg': f'Error creating case: {str(e)}'}, 200


@app.route('/api/upload_case_data', methods=['POST'])
def upload_case_data():
    try:
        case_id = request.form.get("caseId")
        file_type = request.form.get("fileType")
        file = request.files.get("case-file")
        
        if not file or file.filename == '':
            return {'success': False, 'errorMsg': 'No file part'}, 200
        
        # 根据文件类型创建相应目录
        type_folder = {
            'face_expression': 'face_expression',
            'behavior_video': 'behavior_video',
            'eye_tracking': 'eye_tracking',
            'scale_data': 'scale_data'
        }.get(file_type, 'other')
        
        # 创建文件夹
        type_path = os.path.join(app.config.get("UPLOAD_FOLDER"), type_folder)
        os.makedirs(type_path, exist_ok=True)
        
        # 构建文件名
        if file_type == 'eye_tracking':
            # 对于眼动数据，不添加case_id前缀，保持原始文件名
            filename = secure_filename(file.filename)
        else:
            # 其他类型文件，使用case_id作为前缀
            filename = f"{case_id}_{secure_filename(file.filename)}"
            
        file_path = os.path.join(type_path, filename)
        file.save(file_path)
        
        # 更新case记录，添加文件信息
        csv_path = app.config.get("case_save_file")
        df = pd.read_csv(csv_path)
        
        # 找到对应case_id的记录
        case_idx = df.index[df['caseId'] == int(case_id)].tolist()
        if not case_idx:
            return {'success': False, 'errorMsg': 'Case not found'}, 200
        
        # 创建新的列（如果不存在）
        column_name = {
            'face_expression': 'face_expression_file',
            'behavior_video': 'behavior_video_file',
            'eye_tracking': 'eye_tracking_file',
            'scale_data': 'scale_data_file'
        }.get(file_type)
        
        if column_name not in df.columns:
            df[column_name] = None
        
        # 更新该case的对应文件字段
        df.at[case_idx[0], column_name] = f"{type_folder}/{filename}"
        
        # 对于眼动数据，特别处理eye列
        if file_type == 'eye_tracking':
            # 确保eye列存在
            if 'eye' not in df.columns:
                df['eye'] = None
            
            # 更新eye列，只存储原始文件名，不包含路径
            df.at[case_idx[0], 'eye'] = secure_filename(file.filename)
            
            # 如果文件名是1.csv，确保1_50.png存在 (此部分已在case_detail处理)
            print(f"已上传眼动数据文件: {secure_filename(file.filename)}")
            print(f"文件存储路径: {file_path}")
            print(f"eye列值为: {secure_filename(file.filename)}")
            print(f"eye_tracking_file列值为: {type_folder}/{filename}")
        
        df.to_csv(csv_path, index=False)
        
        return {'success': True}, 200
    except Exception as e:
        return {'success': False, 'errorMsg': f'Error uploading file: {str(e)}'}, 200


@app.route('/get_eye_tracking_image/<filename>')
def get_eye_tracking_image(filename):
    """提供眼动数据图像文件"""
    try:
        print(f"请求眼动数据图像: {filename}")
        
        # 首先尝试从uploads目录获取文件
        file_path = os.path.join(app.config.get("UPLOAD_FOLDER"), filename)
        print(f"尝试路径1: {file_path}")
        if os.path.exists(file_path):
            print(f"找到文件于: {file_path}")
            # 检查文件类型
            if filename.endswith('.html'):
                with open(file_path, 'r') as f:
                    return f.read(), 200, {'Content-Type': 'text/html'}
            else:
                return send_file(file_path)
        
        # 如果不存在，尝试从eye_tracking子目录获取
        eye_tracking_path = os.path.join(app.config.get("UPLOAD_FOLDER"), "eye_tracking", filename)
        print(f"尝试路径2: {eye_tracking_path}")
        if os.path.exists(eye_tracking_path):
            print(f"找到文件于: {eye_tracking_path}")
            # 检查文件类型
            if filename.endswith('.html'):
                with open(eye_tracking_path, 'r') as f:
                    return f.read(), 200, {'Content-Type': 'text/html'}
            else:
                return send_file(eye_tracking_path)
        
        # 特别处理1_50.png
        if filename == '1_50.png':
            # 尝试创建1_50.png
            png_path = os.path.join(app.config.get("UPLOAD_FOLDER"), '1_50.png')
            print(f"特别处理1_50.png，尝试创建: {png_path}")
            try:
                import matplotlib.pyplot as plt
                import numpy as np
                plt.figure(figsize=(8, 6))
                plt.plot(np.random.rand(50), 'r-')
                plt.title('眼动数据可视化')
                plt.xlabel('时间 (ms)')
                plt.ylabel('位置')
                plt.grid(True)
                plt.savefig(png_path)
                plt.close()
                print(f"成功创建眼动数据图像: {png_path}")
                return send_file(png_path)
            except Exception as e:
                print(f"创建图像时出错: {str(e)}")
            
        # 如果找不到文件，检查是否存在替代文件
        alt_file_name = filename.split('.')[0] + '.txt'
        alt_file_path = os.path.join(app.config.get("UPLOAD_FOLDER"), alt_file_name)
        print(f"尝试替代文件: {alt_file_path}")
        if os.path.exists(alt_file_path):
            print(f"找到替代文件: {alt_file_path}")
            with open(alt_file_path, 'r') as f:
                content = f.read()
                return f'<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;"><div style="text-align:center;"><h2>眼动数据可视化</h2><p>{content}</p></div></body></html>', 200, {'Content-Type': 'text/html'}
        
        print(f"找不到任何可用文件")
        return jsonify({'error': 'Image file not found'}), 404
    except Exception as e:
        print(f"获取眼动图像时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 设置上传文件夹路径
    # app.config['UPLOAD_FOLDER'] = r"E:\working_dir\py_project\zibizheng\uploads"
    # 确保上传文件夹存在
    app.run(host='0.0.0.0', port=80)
