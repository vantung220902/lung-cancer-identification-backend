from psycopg2._psycopg import connection
import json

def create_prediction(image_url, prediction, confidence, user_id, conn: connection):
    try:
        cur = conn.cursor()
        json_confidence = json.dumps({"values": confidence})
        cur.execute(
            'INSERT INTO prediction (user_id, prediction, image_url,confidence) VALUES (%s, %s, %s, %s)',
            (user_id, prediction, image_url, json_confidence)
        )
        conn.commit()
        cur.close()
        print("Created prediction successfully")
    except Exception as e:
        print("Failed to create prediction")
        print(e)


def find_prediction_by_user_id(user_id, conn: connection):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM prediction WHERE user_id = %s', (user_id,))
        predictions = cur.fetchall()
        cur.close()
        columns = ['id', 'image_url',
                   'prediction', 'confidence', 'user_id',  'created_at']
        map_predictions = [
            dict(zip(columns, prediction)) for prediction in predictions]

        return list(map(lambda prediction: {
            **prediction, 'confidence': prediction['confidence'].get('values', [])},
            map_predictions))
    except Exception as e:
        print("Cannot find prediction by user id")
        print(e)
        return None
