import imageio

def create_gif(input_paths, output_path, duration_between=0.5):
    images = []
    for filename in input_paths:
        images.append(imageio.imread(filename))

    imageio.mimsave(output_path, images, duration=duration_between)
    print('Saved to {}'.format(output_path))

    return output_path

