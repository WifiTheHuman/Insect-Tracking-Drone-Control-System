/****************************************************************************
** Meta object code from reading C++ file 'gazebo_video_stream_widget.h'
**
** Created by: The Qt Meta Object Compiler version 63 (Qt 4.8.7)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../../Tools/sitl_gazebo/include/gazebo_video_stream_widget.h"
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'gazebo_video_stream_widget.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 63
#error "This file was generated using the moc from 4.8.7. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
static const uint qt_meta_data_gazebo__VideoStreamWidget[] = {

 // content:
       6,       // revision
       0,       // classname
       0,    0, // classinfo
       1,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: signature, parameters, type, tag, flags
      27,   26,   26,   26, 0x09,

       0        // eod
};

static const char qt_meta_stringdata_gazebo__VideoStreamWidget[] = {
    "gazebo::VideoStreamWidget\0\0OnButton()\0"
};

void gazebo::VideoStreamWidget::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        Q_ASSERT(staticMetaObject.cast(_o));
        VideoStreamWidget *_t = static_cast<VideoStreamWidget *>(_o);
        switch (_id) {
        case 0: _t->OnButton(); break;
        default: ;
        }
    }
    Q_UNUSED(_a);
}

const QMetaObjectExtraData gazebo::VideoStreamWidget::staticMetaObjectExtraData = {
    0,  qt_static_metacall 
};

const QMetaObject gazebo::VideoStreamWidget::staticMetaObject = {
    { &GUIPlugin::staticMetaObject, qt_meta_stringdata_gazebo__VideoStreamWidget,
      qt_meta_data_gazebo__VideoStreamWidget, &staticMetaObjectExtraData }
};

#ifdef Q_NO_DATA_RELOCATION
const QMetaObject &gazebo::VideoStreamWidget::getStaticMetaObject() { return staticMetaObject; }
#endif //Q_NO_DATA_RELOCATION

const QMetaObject *gazebo::VideoStreamWidget::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->metaObject : &staticMetaObject;
}

void *gazebo::VideoStreamWidget::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_gazebo__VideoStreamWidget))
        return static_cast<void*>(const_cast< VideoStreamWidget*>(this));
    return GUIPlugin::qt_metacast(_clname);
}

int gazebo::VideoStreamWidget::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = GUIPlugin::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 1)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 1;
    }
    return _id;
}
QT_END_MOC_NAMESPACE