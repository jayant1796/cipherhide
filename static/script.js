function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.src = '#';
        preview.style.display = 'none';
    }
}


document.getElementById('encode_image').addEventListener('change', function() {
    previewImage(this, 'encode_preview');
});

document.getElementById('decode_image').addEventListener('change', function() {
    previewImage(this, 'decode_preview');
});
